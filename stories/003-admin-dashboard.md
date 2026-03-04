# Story: Admin Dashboard - React Frontend

## Description
As an administrator, I want a web dashboard to manage read receipt tracking, so that I can view recipients, manage settings, and monitor system health.

## Acceptance Criteria
- [ ] React app created in `admin-dashboard/` directory
- [ ] Login page with token-based authentication
- [ ] Dashboard showing summary statistics
- [ ] Recipients list with search and pagination
- [ ] Ability to add/edit/delete recipients
- [ ] Settings page for global configuration
- [ ] Responsive design (mobile-friendly)

## Technical Notes
- Use React 18+ with Vite for build tooling
- Use React Router for navigation
- Use Axios for API calls
- Use Tailwind CSS or Material-UI for styling
- Implement proper error handling
- Add loading states

## Pages Required
1. **Login** (`/login`)
   - Token input field
   - Submit button
   - Error messages

2. **Dashboard** (`/`)
   - Total recipients count
   - Recent tracking events
   - Quick stats

3. **Recipients** (`/recipients`)
   - List view with pagination
   - Search functionality
   - Add new recipient button
   - Edit/delete actions

4. **Settings** (`/settings`)
   - Toggle tracking on/off
   - Configure allowed domains
   - API key management

## API Endpoints Needed
- `POST /api/admin/login` - Authenticate admin
- `GET /api/admin/recipients` - List recipients
- `POST /api/admin/recipients` - Create recipient
- `PUT /api/admin/recipients/<id>` - Update recipient
- `DELETE /api/admin/recipients/<id>` - Delete recipient
- `GET /api/admin/stats` - Get statistics
- `GET /api/admin/settings` - Get settings
- `PUT /api/admin/settings` - Update settings

## Definition of Done
- [ ] All pages implemented
- [ ] All API integrations working
- [ ] Unit tests for components (Jest)
- [ ] E2E tests for critical flows (Cypress)
- [ ] Code coverage >90%
- [ ] Responsive design verified
- [ ] PR reviewed and approved
