# Story: Analytics Dashboard

## Description
As an administrator, I want an analytics dashboard to visualize read receipt data, so that I can understand email engagement patterns and system performance.

## Acceptance Criteria
- [ ] Analytics page with interactive charts
- [ ] Daily/weekly/monthly view toggle
- [ ] Tracking events over time chart
- [ ] Top recipients by opens chart
- [ ] Geographic distribution map
- [ ] User agent breakdown (email clients)
- [ ] Export data to CSV functionality

## Technical Notes
- Use Chart.js or Recharts for visualizations
- Use date-fns for date manipulation
- Implement date range picker
- Cache API responses for performance
- Use React components from admin dashboard

## Charts Required
1. **Tracking Events Over Time**
   - Line chart
   - Configurable time range
   - Hover tooltips

2. **Top Recipients**
   - Bar chart
   - Top 10 recipients
   - Click to drill down

3. **Geographic Distribution**
   - World map or choropleth
   - Country-level data
   - Color-coded by event count

4. **Email Client Breakdown**
   - Pie or donut chart
   - Gmail, Outlook, Yahoo, etc.
   - Percentage display

## API Endpoints Needed
- `GET /api/analytics/summary` - Overall summary stats
- `GET /api/analytics/events` - Time-series event data
- `GET /api/analytics/recipients` - Top recipients
- `GET /api/analytics/geo` - Geographic data
- `GET /api/analytics/clients` - Email client breakdown
- `GET /api/analytics/export` - CSV export

## Definition of Done
- [ ] All charts implemented
- [ ] Data updates in real-time (or near real-time)
- [ ] Responsive design
- [ ] Unit tests for components
- [ ] E2E tests for analytics flows
- [ ] Performance optimized (lazy loading)
- [ ] PR reviewed and approved
