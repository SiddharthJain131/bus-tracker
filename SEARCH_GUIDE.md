# 🔍 Enhanced Search Guide

## Dropdown-Based Search

The Admin and Teacher dashboards now support advanced search using a two-field approach:
1. **Search By** dropdown - Select which field to search in
2. **Search For** input - Enter your search term

### Search Fields

#### Admin Dashboard - Students Tab
Available in "Search By" dropdown:
- **All Fields** - Search across all fields (default)
- **Name** - Search by student name
- **Roll No** - Search by roll number
- **Bus** - Search by bus number
- **Class** - Search by class name
- **Parent** - Search by parent name
- **Teacher** - Search by teacher name

#### Teacher Dashboard - Students Tab
Available in "Search By" dropdown:
- **All Fields** - Search across all fields (default)
- **Name** - Search by student name
- **Roll No** - Search by roll number
- **Bus** - Search by bus number
- **Parent** - Search by parent name

### How to Use

1. Select a field from the **"Search By"** dropdown
2. Type your search term in the **"Search For"** input box
3. Results update automatically as you type

### Examples

| Search By | Search For | Result |
|-----------|------------|--------|
| Bus | BUS-001 | Shows all students on bus BUS-001 |
| Roll No | G5A | Shows all students with roll numbers containing G5A |
| Class | 5 | Shows all Grade 5 students |
| Parent | john | Shows students whose parent name contains "john" |
| Teacher | mary | Shows students whose teacher name contains "mary" |
| All Fields | Emma | Searches "Emma" across all fields (name, parent, class, bus, roll) |

### All Fields Search

When "All Fields" is selected (default), the search looks in:
- Student name
- Parent name
- Class name
- Bus number
- Roll number

Example: Selecting "All Fields" and typing `Emma` will find students named Emma, or with parent named Emma, etc.

### UI Changes

#### Teacher Dashboard
- **Roll No column moved to first position** for better visibility
- Roll number now shows as first column with emerald-700 color
- Same formatting as other columns (text-sm) but retains the distinctive color

#### Search Input
- Expanded width in Admin Dashboard (w-96)
- Helpful placeholder text showing example searches
- Tooltip on hover explaining all available parameters

## Notes

- Search is **case-insensitive**
- Partial matches are supported (e.g., `bus:BUS` matches BUS-001, BUS-002)
- Only one parameter can be used at a time
- Filters (AM Status, PM Status, Bus) work in combination with search
