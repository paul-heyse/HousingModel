## Context
The Aker property model requires a comprehensive operations and brand management dashboard to monitor reputation metrics, manage review data, and configure reputation-driven pricing strategies. Project.md section 5 specifies "NPS loop → pricing/features; reputation lift reduces concessions & speeds lease" and "Feedback ingestion (reviews/NPS) → Reputation Index → pricing guardrails". The current system lacks a unified interface for operations teams to track brand health and make data-informed operational decisions.

## Goals / Non-Goals
- **Goals**:
  - Provide centralized reputation and brand monitoring interface
  - Enable efficient review data ingestion and validation
  - Support reputation-driven pricing strategy configuration
  - Maintain real-time operational decision-making capabilities
  - Integrate seamlessly with existing ops engine and data systems
- **Non-Goals**:
  - Replace existing ops engine functionality
  - Implement real-time collaboration features
  - Create advanced analytics or ML-based insights

## Decisions

### Dashboard Architecture
- **Single Page Application**: Comprehensive dashboard with multiple data views
- **Real-time Updates**: Live data refresh for reputation metrics
- **Modular Components**: Reusable chart and data components
- **State Management**: URL-based state with localStorage persistence

### API Integration Strategy
- **RESTful Endpoints**: Clean API contracts for reputation and pricing data
- **CSV Processing**: Server-side validation and bulk import
- **Live Data**: Database connections for real-time updates
- **Error Handling**: Comprehensive error reporting and recovery

### Data Flow Architecture
```
User Interaction → API Call → Data Processing → UI Update → State Persistence
     ↓              ↓              ↓              ↓              ↓
  Dashboard → /api/ops/reputation → Python Engine → Chart Render → localStorage
  Upload   → /api/ops/reviews/upload → Validation → Metrics Update → Cache
  Slider   → /api/ops/pricing/preview → Guardrail Calc → Table Update → None
```

## Implementation Strategy

### Phase 1: Core Dashboard Infrastructure
```python
# Main dashboard application
class OpsBrandDashboard:
    def __init__(self, app: Dash):
        self.app = app
        self._setup_routes()
        self._setup_layout()

    def _setup_routes(self):
        @self.app.server.route('/api/ops/reputation')
        def get_reputation():
            asset_id = request.args.get('asset_id')
            return get_reputation_data(asset_id)

        @self.app.server.route('/api/ops/reviews/upload', methods=['POST'])
        def upload_reviews():
            file = request.files.get('file')
            return process_csv_upload(file)
```

### Phase 2: Data Integration
- **Database Queries**: Optimized queries for reputation and review data
- **Caching Layer**: Redis/in-memory caching for frequently accessed data
- **Data Transformation**: Python-to-UI data mapping and formatting
- **Real-time Updates**: WebSocket or polling for live data refresh

### Phase 3: UI Components
- **Chart Library**: Plotly.js for interactive visualizations
- **Form Components**: Dash components for data input and filtering
- **Layout System**: Bootstrap-based responsive grid system
- **State Management**: React-like state handling in Dash callbacks

### Phase 4: Interactive Features
- **CSV Upload**: Drag-and-drop file handling with progress indicators
- **Real-time Charts**: Dynamic chart updates based on data changes
- **What-if Analysis**: Interactive sliders for scenario modeling
- **Error Display**: User-friendly error messages and validation feedback

## API Contracts

### GET /api/ops/reputation
**Purpose**: Retrieve reputation metrics and pricing rules for an asset
**Query Parameters**:
- `asset_id` (required): Asset identifier
- `start_date` (optional): Start of date range (default: 12 months ago)
- `end_date` (optional): End of date range (default: today)
- `sources` (optional): Comma-separated list of review sources

**Response Format**:
```json
{
  "reputation_idx": 78.5,
  "nps_series": [
    {"date": "2024-01-01", "nps": 25},
    {"date": "2024-02-01", "nps": 30}
  ],
  "reviews_series": [
    {"date": "2024-01-01", "rating": 4.2, "volume": 15},
    {"date": "2024-02-01", "rating": 4.1, "volume": 18}
  ],
  "pricing_rules": {
    "max_concession_days": 7,
    "floor_price_pct": 5.0,
    "premium_cap_pct": 8.0
  }
}
```

### POST /api/ops/reviews/upload
**Purpose**: Upload and process CSV review data
**Content-Type**: multipart/form-data
**Request Body**:
- `file`: CSV file with required columns

**Response Format**:
```json
{
  "ingested": 45,
  "rejected": 3,
  "sample_errors": [
    {"row": 12, "error": "rating outside 1-5 range"},
    {"row": 18, "error": "invalid date format"}
  ]
}
```

### GET /api/ops/pricing/preview
**Purpose**: Preview pricing guardrails for hypothetical reputation index
**Query Parameters**:
- `asset_id` (required): Asset identifier
- `reputation_idx` (required): Hypothetical reputation index (0-100)

**Response Format**:
```json
{
  "guardrails": {
    "max_concession_days": 5,
    "floor_price_pct": 3.0,
    "premium_cap_pct": 6.0
  },
  "based_on_reputation": 85.0
}
```

## CSV Schema Requirements

### Required Columns
- `date`: Date in YYYY-MM-DD format
- `source`: Review source (e.g., "Google", "Yelp", "Apartments.com")
- `rating`: Numeric rating 1-5 (float allowed)
- `text`: Review text content
- `response_time_days`: Days to respond to review (optional, defaults to 0)
- `is_move_in`: Boolean indicating if review is from move-in period

### Validation Rules
- **Date Format**: Must be valid YYYY-MM-DD
- **Source**: Must be non-empty string
- **Rating**: Must be numeric between 1.0 and 5.0
- **Text**: Must be non-empty string (minimum 10 characters)
- **Response Time**: Must be non-negative integer (defaults to 0 if missing)
- **Is Move-in**: Must be boolean (true/false, 1/0, yes/no)

### Error Reporting
- Row-by-row validation with specific error messages
- Sample error display (first 5 errors shown)
- Detailed error categorization (format, range, required field)

## UI Component Specifications

### Top Controls Bar
- **Date Range Picker**: Default 12-month range, URL-persisted
- **Source Filter**: Multi-select dropdown for review sources
- **Upload Button**: File input with drag-and-drop support
- **Template Download**: Link to CSV template file

### Left Column (Charts)
- **NPS Trend Chart**: Line chart showing NPS over time
- **Reviews Volume/Rating Chart**: Dual-axis with volume bars and rating line

### Right Column (Metrics & Controls)
- **Reputation Index Gauge**: Circular gauge with color-coded ranges
- **Pricing Rules Table**: Current guardrail settings
- **What-if Slider**: Interactive reputation index adjustment
- **Preview Rules Table**: Updated guardrails based on slider value

### Error States
- **No Data State**: "No data for selected range" with upload prompt
- **Upload Errors**: Expandable error table with sample issues
- **Loading States**: Progress indicators for API calls
- **Permission Errors**: Clear messaging for role restrictions

## Security Considerations

### Role-Based Access
- **Viewer Role**: Read-only access to all dashboard data
- **Analyst Role**: Full access including CSV upload and data modification
- **Admin Role**: All permissions plus system configuration access

### Data Protection
- **Review Text**: Not logged in telemetry or audit trails
- **Upload Limits**: File size and row count restrictions
- **Rate Limiting**: API call frequency limits per user
- **Input Sanitization**: All user inputs validated and sanitized

### Audit Trail
- Upload attempts and success/failure rates logged
- User actions tracked for compliance reporting
- Data modification events recorded with before/after values

## Performance Optimization

### Data Caching
- API responses cached for 5-15 minutes based on data volatility
- Chart data pre-computed and cached for common time ranges
- User preferences cached in localStorage

### Lazy Loading
- Charts render with placeholder data, then populate asynchronously
- Large datasets loaded incrementally
- Pagination for review history and error logs

### Memory Management
- Large CSV files processed in chunks
- Temporary data cleaned up after processing
- Memory usage monitored and optimized

## Testing Strategy

### Unit Tests
- Component rendering and state management
- API endpoint functionality and error handling
- CSV validation logic and edge cases
- Chart data processing and formatting

### Integration Tests
- End-to-end workflow from upload to visualization
- Database integration and data consistency
- API contract compliance and error responses
- Cross-component data flow validation

### End-to-End Tests (Playwright)
- Complete user workflows from navigation to data visualization
- File upload and processing workflows
- Interactive slider and preview functionality
- Error state handling and recovery

### Performance Tests
- Large dataset processing benchmarks
- Concurrent user load testing
- Memory usage validation under stress
- API response time monitoring

## Migration Plan

1. **Phase 1**: Core dashboard structure and API endpoints (Week 1-2)
2. **Phase 2**: Chart implementation and data visualization (Week 3-4)
3. **Phase 3**: CSV upload and validation functionality (Week 5-6)
4. **Phase 4**: What-if analysis and advanced interactions (Week 7-8)
5. **Phase 5**: Testing, performance optimization, and deployment (Week 9-10)

### Rollback Strategy
- Feature flags control dashboard availability
- Database migrations can be rolled back if needed
- Gradual rollout by user role and asset type

## Dependencies

### New Dependencies
- **pandas**: CSV processing and data manipulation
- **openpyxl**: Excel file generation for templates
- **plotly**: Interactive chart rendering
- **dash-uploader**: Enhanced file upload capabilities

### Existing Dependencies
- **aker_core.ops**: Reputation index calculation and pricing rules
- **aker_core.database**: Data access and query optimization
- **aker_gui**: Base dashboard framework and components

This implementation will create a comprehensive Ops & Brand dashboard that provides operations teams with the tools they need to monitor brand health, manage reputation data, and optimize pricing strategies based on real-time reputation metrics.
