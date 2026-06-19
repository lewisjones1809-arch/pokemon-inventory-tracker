# TODO

## Features
- [ ] Price-history chart (headline feature, not yet visible)
- [ ] README with screenshot + architecture overview
- [ ] Filtering on inventory cards
- [ ] Settings page - reset DB, reinsert manual cards
- [ ] Purchase form live drop down from API query
- [ ] Sales form live drop down from owned cards

## Polish
- [ ] Fix double calc_fifo_cost call (computed twice per card)
- [ ] Clean up _x / _y column names from merges
- [ ] Add success/error feedback on purchase & sale forms
- [ ] Handle invalid Card ID gracefully (clear error, not traceback)

## Later / nice-to-have
- [ ] @st.cache_resource for the DB connection
- [ ] Deploy live (Streamlit Community Cloud)