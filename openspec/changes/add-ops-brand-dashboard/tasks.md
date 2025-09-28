## 1. Specification & Design
- [x] 1.1 Update GUI spec with Ops & Brand dashboard scenarios covering navigation, data contracts, interactions, and error states
- [x] 1.2 Document API contracts for reputation endpoints and CSV upload processing
- [x] 1.3 Define data flow for reputation calculation and pricing guardrail integration
- [x] 1.4 Validate change with `openspec validate add-ops-brand-dashboard --strict`

## 2. Backend API Implementation
- [x] 2.1 Implement GET /api/ops/reputation endpoint with reputation index, NPS series, and pricing rules
- [x] 2.2 Create POST /api/ops/reviews/upload endpoint with CSV processing and validation
- [x] 2.3 Build GET /api/ops/pricing/preview endpoint for what-if scenario modeling
- [x] 2.4 Add database schema enhancements for reputation tracking and review storage
- [x] 2.5 Integrate with existing ops engine for reputation index calculation

## 3. Frontend Dashboard Implementation
- [x] 3.1 Create /app/ops route with breadcrumb navigation and asset ID parameter handling
- [x] 3.2 Build top controls bar with date range picker, source filter, and CSV upload button
- [x] 3.3 Implement left column with NPS trend chart and reviews volume/rating dual-axis chart
- [x] 3.4 Create right column with reputation index gauge and pricing rules table
- [x] 3.5 Add what-if slider component with live preview of pricing guardrails

## 4. Interactive Features & State Management
- [x] 4.1 Implement CSV upload functionality with file processing and error reporting
- [x] 4.2 Create what-if slider callback for pricing preview updates
- [x] 4.3 Add URL query parameter handling for date range and asset filtering
- [x] 4.4 Implement dcc.Store caching for upload results and dashboard state
- [x] 4.5 Add localStorage integration for persistent dashboard preferences

## 5. Error Handling & Edge Cases
- [x] 5.1 Implement no-data states for charts with appropriate messaging
- [x] 5.2 Create CSV validation error display with row-specific error messages
- [x] 5.3 Add loading states for API calls and file processing
- [x] 5.4 Handle network errors and API failures gracefully
- [x] 5.5 Implement role-based permission checks for upload functionality

## 6. Data Visualization & Charts
- [x] 6.1 Create NPS trend line chart with time series data
- [x] 6.2 Build dual-axis chart for review volume (bars) and average rating (line)
- [x] 6.3 Implement reputation index gauge with color-coded ranges
- [x] 6.4 Add interactive pricing rules table with conditional formatting
- [x] 6.5 Create responsive chart layouts for different screen sizes

## 7. CSV Processing & Validation
- [x] 7.1 Implement CSV schema validation (date, source, rating, text, response_time_days, is_move_in)
- [x] 7.2 Add data type validation and range checking for all fields
- [x] 7.3 Create error reporting with specific row numbers and validation messages
- [x] 7.4 Implement CSV template download functionality
- [x] 7.5 Add batch processing for large CSV files

## 8. Security & Permissions
- [x] 8.1 Implement role-based access control for upload functionality
- [x] 8.2 Add telemetry logging for upload attempts and error rates
- [x] 8.3 Ensure no sensitive data logging in review text processing
- [x] 8.4 Add API rate limiting and abuse prevention
- [x] 8.5 Implement secure file upload handling

## 9. Testing & Quality Assurance
- [x] 9.1 Create Playwright end-to-end tests for complete dashboard workflow
- [x] 9.2 Implement API contract tests for all endpoints
- [x] 9.3 Add CSV validation test suite with edge cases
- [x] 9.4 Create golden master tests for chart rendering consistency
- [x] 9.5 Add performance tests for large dataset handling
- [x] 9.6 Implement accessibility testing for dashboard components

## 10. Documentation & Deployment
- [x] 10.1 Document API endpoints and data contracts
- [x] 10.2 Create user guide for dashboard functionality
- [x] 10.3 Add troubleshooting guide for common issues
- [x] 10.4 Create deployment configurations for production environment
- [x] 10.5 Add monitoring and alerting for dashboard health
