# 🔍 Enhanced Search Guide

## Parameter-Based Search

The Admin and Teacher dashboards now support advanced search using parameters.

### Search Syntax

Use the format: `parameter:value`

### Available Parameters

#### Admin Dashboard - Students Tab
- `bus:BUS-001` - Search by bus number
- `roll:G5A-001` - Search by roll number
- `name:Emma` - Search by student name
- `class:5` - Search by class
- `parent:John` - Search by parent name
- `teacher:Mary` - Search by teacher name

#### Teacher Dashboard - Students Tab
- `bus:BUS-001` - Search by bus number
- `roll:G5A-001` - Search by roll number
- `name:Emma` - Search by student name
- `parent:John` - Search by parent name

### Examples

| Search Query | Result |
|--------------|--------|
| `bus:BUS-001` | Shows all students on bus BUS-001 |
| `roll:G5A` | Shows all students with roll numbers starting with G5A |
| `class:5` | Shows all Grade 5 students |
| `parent:john` | Shows students whose parent name contains "john" |
| `teacher:mary` | Shows students whose teacher name contains "mary" |
| `Emma` | Default search: Shows students matching "Emma" in any field |

### Default Search (No Parameters)

When you search without using parameters, the system searches across:
- Student name
- Parent name
- Class name
- Bus number
- Roll number

Example: Typing `Emma` will find students named Emma, or with parent named Emma, etc.

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
