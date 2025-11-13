import { useState, useCallback } from 'react';
import { toast } from 'sonner';

/**
 * Custom hook for managing modal form state and operations
 * Handles common patterns: loading state, form data, submission, error handling
 * 
 * @param {Object} initialFormData - Initial form data structure
 * @param {Function} onSubmitCallback - Async function to call on form submit
 * @param {Function} onSuccessCallback - Callback after successful submission
 * @param {Function} onCloseCallback - Callback when modal closes
 * @returns {Object} Form state and handlers
 */
export function useModalForm(
  initialFormData = {},
  onSubmitCallback,
  onSuccessCallback,
  onCloseCallback
) {
  const [formData, setFormData] = useState(initialFormData);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  /**
   * Update a single form field
   */
  const updateField = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field if it exists
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  }, [errors]);

  /**
   * Update multiple form fields at once
   */
  const updateFields = useCallback((updates) => {
    setFormData(prev => ({ ...prev, ...updates }));
  }, []);

  /**
   * Reset form to initial data
   */
  const resetForm = useCallback(() => {
    setFormData(initialFormData);
    setErrors({});
    setLoading(false);
  }, [initialFormData]);

  /**
   * Validate required fields
   * @param {Array<string>} requiredFields - Array of field names that are required
   * @returns {boolean} True if all required fields are filled
   */
  const validateRequired = useCallback((requiredFields) => {
    const newErrors = {};
    let isValid = true;

    requiredFields.forEach(field => {
      if (!formData[field] || formData[field].toString().trim() === '') {
        newErrors[field] = 'This field is required';
        isValid = false;
      }
    });

    setErrors(newErrors);
    
    if (!isValid) {
      toast.error('Please fill in all required fields');
    }

    return isValid;
  }, [formData]);

  /**
   * Handle form submission with error handling
   * @param {Event} e - Form submit event
   * @param {Array<string>} requiredFields - Optional array of required field names
   */
  const handleSubmit = useCallback(async (e, requiredFields = []) => {
    if (e) {
      e.preventDefault();
    }

    // Validate if required fields are provided
    if (requiredFields.length > 0 && !validateRequired(requiredFields)) {
      return;
    }

    setLoading(true);
    try {
      const result = await onSubmitCallback(formData);
      
      if (onSuccessCallback) {
        onSuccessCallback(result);
      }
      
      if (onCloseCallback) {
        onCloseCallback();
      }
      
      return result;
    } catch (error) {
      console.error('Form submission error:', error);
      
      // Handle different error formats
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.message || 
        error.message || 
        'An error occurred. Please try again.';
      
      toast.error(errorMessage);
      
      // If backend returns field-specific errors
      if (error.response?.data?.errors) {
        setErrors(error.response.data.errors);
      }
      
      throw error;
    } finally {
      setLoading(false);
    }
  }, [formData, onSubmitCallback, onSuccessCallback, onCloseCallback, validateRequired]);

  /**
   * Handle modal close with cleanup
   */
  const handleClose = useCallback(() => {
    resetForm();
    if (onCloseCallback) {
      onCloseCallback();
    }
  }, [resetForm, onCloseCallback]);

  return {
    formData,
    setFormData,
    loading,
    setLoading,
    errors,
    setErrors,
    updateField,
    updateFields,
    resetForm,
    validateRequired,
    handleSubmit,
    handleClose,
  };
}

/**
 * Custom hook for managing data fetching in modals
 * Handles loading state and error handling for API calls
 * 
 * @returns {Object} Fetch state and handlers
 */
export function useModalData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Fetch data with error handling
   * @param {Function} fetchFunction - Async function that fetches data
   * @param {Object} options - Options for fetching
   */
  const fetchData = useCallback(async (fetchFunction, options = {}) => {
    const { showError = true, onSuccess, onError } = options;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetchFunction();
      setData(result);
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      return result;
    } catch (err) {
      console.error('Data fetch error:', err);
      setError(err);
      
      if (showError) {
        const errorMessage = 
          err.response?.data?.detail || 
          err.response?.data?.message || 
          err.message || 
          'Failed to load data';
        
        toast.error(errorMessage);
      }
      
      if (onError) {
        onError(err);
      }
      
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Reset data state
   */
  const resetData = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    setData,
    loading,
    error,
    fetchData,
    resetData,
  };
}
