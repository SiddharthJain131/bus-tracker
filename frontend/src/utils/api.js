import axios from 'axios';
import { toast } from 'sonner';

/**
 * Common API utility functions
 * Provides reusable functions for common API operations with consistent error handling
 */

/**
 * Handle API errors consistently
 * @param {Error} error - The error object from axios
 * @param {string} defaultMessage - Default message if no specific error is found
 * @returns {string} The error message to display
 */
export const handleApiError = (error, defaultMessage = 'An error occurred') => {
  console.error('API Error:', error);
  
  const errorMessage = 
    error.response?.data?.detail || 
    error.response?.data?.message || 
    error.message || 
    defaultMessage;
  
  return errorMessage;
};

/**
 * Make an API call with consistent error handling
 * @param {Function} apiCall - Async function that makes the API call
 * @param {Object} options - Options for the API call
 * @returns {Promise} Result of the API call
 */
export const makeApiCall = async (apiCall, options = {}) => {
  const {
    successMessage,
    errorMessage = 'Operation failed',
    showSuccessToast = true,
    showErrorToast = true,
    onSuccess,
    onError,
  } = options;

  try {
    const result = await apiCall();
    
    if (showSuccessToast && successMessage) {
      toast.success(successMessage);
    }
    
    if (onSuccess) {
      onSuccess(result);
    }
    
    return result;
  } catch (error) {
    const message = handleApiError(error, errorMessage);
    
    if (showErrorToast) {
      toast.error(message);
    }
    
    if (onError) {
      onError(error);
    }
    
    throw error;
  }
};

/**
 * Fetch data from an endpoint
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Axios config options
 * @returns {Promise} The response data
 */
export const fetchData = async (url, options = {}) => {
  try {
    const response = await axios.get(url, options);
    return response.data;
  } catch (error) {
    const message = handleApiError(error, 'Failed to fetch data');
    toast.error(message);
    throw error;
  }
};

/**
 * Create a new resource
 * @param {string} url - The API endpoint URL
 * @param {Object} data - The data to send
 * @param {Object} options - Additional options
 * @returns {Promise} The response data
 */
export const createResource = async (url, data, options = {}) => {
  const { successMessage = 'Created successfully!', ...axiosOptions } = options;
  
  return makeApiCall(
    () => axios.post(url, data, axiosOptions),
    { successMessage }
  );
};

/**
 * Update an existing resource
 * @param {string} url - The API endpoint URL
 * @param {Object} data - The data to send
 * @param {Object} options - Additional options
 * @returns {Promise} The response data
 */
export const updateResource = async (url, data, options = {}) => {
  const { successMessage = 'Updated successfully!', ...axiosOptions } = options;
  
  return makeApiCall(
    () => axios.put(url, data, axiosOptions),
    { successMessage }
  );
};

/**
 * Delete a resource
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Additional options
 * @returns {Promise} The response data
 */
export const deleteResource = async (url, options = {}) => {
  const { successMessage = 'Deleted successfully!', confirmMessage, ...axiosOptions } = options;
  
  if (confirmMessage && !window.confirm(confirmMessage)) {
    return Promise.reject(new Error('Deletion cancelled'));
  }
  
  return makeApiCall(
    () => axios.delete(url, axiosOptions),
    { successMessage }
  );
};

/**
 * Upload a file
 * @param {string} url - The API endpoint URL
 * @param {File} file - The file to upload
 * @param {Object} options - Additional options
 * @returns {Promise} The response data
 */
export const uploadFile = async (url, file, options = {}) => {
  const {
    successMessage = 'File uploaded successfully!',
    fieldName = 'file',
    additionalData = {},
    onUploadProgress,
    ...axiosOptions
  } = options;

  const formData = new FormData();
  formData.append(fieldName, file);
  
  // Add any additional fields to the form data
  Object.keys(additionalData).forEach(key => {
    formData.append(key, additionalData[key]);
  });

  return makeApiCall(
    () => axios.post(url, formData, {
      ...axiosOptions,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...axiosOptions.headers,
      },
      onUploadProgress,
    }),
    { successMessage }
  );
};

/**
 * Fetch multiple resources in parallel
 * @param {Array<Function>} fetchFunctions - Array of async functions that fetch data
 * @param {Object} options - Options for error handling
 * @returns {Promise<Array>} Array of results
 */
export const fetchMultiple = async (fetchFunctions, options = {}) => {
  const { showErrorToast = true } = options;
  
  try {
    const results = await Promise.all(fetchFunctions.map(fn => fn()));
    return results;
  } catch (error) {
    if (showErrorToast) {
      const message = handleApiError(error, 'Failed to load data');
      toast.error(message);
    }
    throw error;
  }
};

/**
 * Check if an API error is a specific status code
 * @param {Error} error - The error object
 * @param {number} statusCode - The status code to check
 * @returns {boolean} True if the error has the specified status code
 */
export const isStatusCode = (error, statusCode) => {
  return error.response?.status === statusCode;
};

/**
 * Check if an API error is a validation error (400)
 * @param {Error} error - The error object
 * @returns {boolean} True if it's a validation error
 */
export const isValidationError = (error) => isStatusCode(error, 400);

/**
 * Check if an API error is an authorization error (403)
 * @param {Error} error - The error object
 * @returns {boolean} True if it's an authorization error
 */
export const isAuthorizationError = (error) => isStatusCode(error, 403);

/**
 * Check if an API error is a not found error (404)
 * @param {Error} error - The error object
 * @returns {boolean} True if it's a not found error
 */
export const isNotFoundError = (error) => isStatusCode(error, 404);
