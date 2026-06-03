import sqlite3
import pandas as pd
import plotext as plt
import os

def show_population_graph(target_run_name):
    """Generates a terminal-based line graph of population over time."""
    db_path = "data/ecosystem.db"
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Resolve Run Name to internal ID
    cursor.execute("SELECT id FROM runs WHERE name = ?", (target_run_name,))
    result = cursor.fetchone()

    if not result:
        print(f"Error: Run named '{target_run_name}' not found.")
        conn.close()
        return

    target_run_id = result[0]

    # 2. SQL Query for population counts
    query = f"""
    SELECT 
        t.tick_number, 
        cs.species, 
        COUNT(cs.creature_id) as species_count
    FROM ticks t
    JOIN creature_states cs ON t.id = cs.tick_id
    WHERE t.run_id = ?
    GROUP BY t.tick_number, cs.species
    ORDER BY t.tick_number
    """
    
    species_df = pd.read_sql_query(query, conn, params=(target_run_id,))
    conn.close()

    if species_df.empty:
        print(f"No creature data found for '{target_run_name}'.")
        return

    # 3. Pivot the data for plotting
    pivot_df = species_df.pivot(index='tick_number', columns='species', values='species_count').fillna(0)

    # 4. Create the Terminal Graph
    plt.clear_data()
    plt.theme("matrix") # Green terminal theme
    
    # Plot Erf (Prey)
    if 'erf' in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df['erf'], label='ERF (Prey)', color="green+")
    
    # Plot Glooper (Predator)
    if 'glooper' in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df['glooper'], label='GLOOPER (Predator)', color="red")

    plt.title(f"Population Dynamics: {target_run_name}")
    plt.xlabel("Tick Number")
    plt.ylabel("Count")
    plt.show()

    # 5. Summary Stats (Quick reference for your presentation)
    print(f"\n--- Stats: {target_run_name} ---")
    for col in pivot_df.columns:
        print(f"{col.upper()}: Final {int(pivot_df[col].iloc[-1])} | Peak {int(pivot_df[col].max())}")