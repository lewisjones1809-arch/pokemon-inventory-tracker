# TODO

## Features
- [ ] Price-history chart (headline feature, not yet visible)
- [x] README with screenshot + architecture overview
- [ ] Filtering on inventory cards
- [x] Settings page - reset DB, reinsert manual cards
- [ ] Purchase form live drop down from API query
- [ ] Sales form live drop down from owned cards

## Polish
- [x] Fix double calc_fifo_cost call (computed twice per card)
- [x] Clean up _x / _y column names from merges
- [ ] Add success/error feedback on purchase & sale forms
- [ ] Handle invalid Card ID gracefully (clear error, not traceback)
- [x] Improve speed of inventory panel

## Later / nice-to-have
- [x] @st.cache_resource for the DB connection
- [ ] Deploy live (Streamlit Community Cloud)

## v2 Features
- [ ] Japanese Cards
- [ ] Korean Cards