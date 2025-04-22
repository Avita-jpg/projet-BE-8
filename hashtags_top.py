import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Pour le formatage français
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

def afficher_hashtag_ids_top():
    st.title("🏷️ Hashtag les plus utilisés")

    try:
        df = pd.read_csv("Hashtag_clean.csv")
    except FileNotFoundError:
        st.error("Fichier Hashtag_clean.csv introuvable.")
        return

    # Vérification des colonnes nécessaires
    required_columns = {"hashtag_id", "occurences"}
    if not required_columns.issubset(df.columns):
        st.error("Colonnes attendues manquantes dans le fichier.")
        return

    # Nettoyage des hashtags
    df['hashtag_id'] = df['hashtag_id'].str.lower().str.strip()

    # Comptage des occurrences
    top_hashtag_ids = df.groupby('hashtag_id')['occurences'].sum().reset_index()
    top_hashtag_ids = top_hashtag_ids.sort_values(by='occurences', ascending=False)

    # Nombre à afficher (paramètre interactif)
    top_n = st.slider("Nombre de hashtag à afficher", min_value=5, max_value=30, value=10)

    # Affichage graphique
    fig = px.bar(top_hashtag_ids.head(top_n),
                 x='occurences',
                 y='hashtag_id',
                 orientation='h',
                 title=f"Top {top_n} des hashtags les plus utilisés",
                 labels={'occurences': 'Nombre d’occurrences', 'hashtag_id': 'Hashtag'})

    fig.update_layout(yaxis={'categoryorder':'total ascending'}, title_x=0.5)

    st.plotly_chart(fig, use_container_width=True)

    # Tableau des hashtag_ids
    st.subheader("📋 Tableau des hashtags")
    st.dataframe(top_hashtag_ids.head(top_n), use_container_width=True)
