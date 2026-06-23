import streamlit as st
from functions import reset_table, get_connection, get_inventory, insert_dummy
from load_inventory import load_inventory_from_pd
import pandas as pd

con = get_connection()

st.title('Settings')

inv_csv = st.file_uploader('Upload Inventory', type='.csv')

if inv_csv is not None:
    df = pd.read_csv(inv_csv)
    required = {'name','set','cn','finishType','condition','quantity','language','price'}

    if not required.issubset(df.columns):
        st.error(f'CSV missing columns: {required - set(df.columns)}')
    else:
        st.write(f'Found {len(df)} rows ({(df['language'] == 'English').sum()} English)')

    if st.button('Import'):
        with st.status("Importing...", expanded=True) as status:
            def set_status(msg):
                status.update(label=msg)
                status.write(msg)

        bar = st.progress(0.0)

        def row_progress(fraction):
            bar.progress(fraction)
    
        counter, skipped, failed, failures = load_inventory_from_pd(con, df, set_status=set_status, row_progress=row_progress)
        status.update(label="Import complete!", state="complete")
        st.success(f"Imported {counter}, skipped {skipped}, failed {failed}")

        if failures:
            st.download_button("Download failures", pd.DataFrame(failures).to_csv(index=False), "failures.csv")
        get_inventory.clear()


table = st.selectbox('Reset Table:', ['allCards', 'cardVariants', 'purchases', 'sales', 'listedPrices', 'priceHistory', 'importedSets'])
st.button('Reset Table', on_click=reset_table, args=(con, table))

st.button('Insert Dummy Data', on_click=insert_dummy)


