# Story: Test Coverage >90%

## Description
As a developer, I want comprehensive test coverage for all code, so that we can confidently refactor and extend the codebase without introducing bugs.

## Acceptance Criteria
- [ ] All Flask routes have unit tests
- [ ] All models have unit tests
- [ ] All utility functions have unit tests
- [ ] Integration tests for critical paths
- [ ] Coverage report shows >90% line coverage
- [ ] Coverage report shows >80% branch coverage

## Technical Notes
- Use `pytest` as the testing framework
- Use `pytest-cov` for coverage reporting
- Mock external dependencies (database, APIs)
- Use fixtures for common test setup

## Test Areas
1. **Flask Routes**
   - `/` - root path
   - `/new-uuid` - UUID generation
   - `/img/<uuid>` - tracking pixel endpoint
   
2. **Models**
   - `Recipients` model
   - `Tracking` model
   
3. **Utilities**
   - `nocache` decorator
   - UUID generation
   - Image creation

## Definition of Done
- [ ] All tests pass
- [ ] Coverage >90%
- [ ] Tests run in CI pipeline
- [ ] No flaky tests
