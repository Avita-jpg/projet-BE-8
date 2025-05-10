import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px


def afficher_statistiques_globales(dataframes,labels):
    st.title("📊 Statistiques globales")

    # Vérification si les données sont présentes
    if "Tweet_sentiment_localisation" not in dataframes:
        st.error("Le fichier 'Tweet_sentiment_localisation.csv' est manquant.")
        return

    # Chargement des données
    df = dataframes["Tweet_sentiment_localisation"]
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["topic"] = df["topic"].map(labels).fillna(df["topic"])

    

    #Chargement des données
    total_tweets = len(df)
    date_min = df["created_at"].min().date()
    date_max = df["created_at"].max().date()
    nb_topics = df["topic"].nunique()
    total_retweets = int(df["retweet_count"].sum())
    total_likes = int(df["favorite_count"].sum())
    nb_annotated = df["annotation_annotated"].sum()
    nb_high_priority = df[df["annotation_postPriority"] == "High"].shape[0]
    nb_sensitive = df["possibly_sensitive"].sum()

    #Affichage des données
    col1,col2= st.columns(2,border=True,gap="large")
    col3,col4= st.columns(2,border=True,gap="large")
    with col1:
        st.write("🐤 Tweets au total", f"{total_tweets:n}")
        st.write("🗓️ Période couverte", f"{date_min} → {date_max}")
        st.write("🔥 Crises détectées", f"{nb_topics}")    
        st.write("🔁 Retweets totaux", f"{total_retweets:n}")
        st.write("❤️ Likes totaux", f"{total_likes:n}")
        st.write("🚨 Tweets sensibles", f"{int(nb_sensitive)}")
        st.write(f"- Tweets annotés : **{int(nb_annotated)}**")
        st.write(f"- Tweets de priorité haute : **{nb_high_priority}**")
    with col2:
        afficher_statistiques_temps(df)
    with col3:
        create_heatmap(df)
    with col4: 
        afficherHashtag(dataframes)
    afficher_repartition_par_topic(df)

def create_heatmap(df):
    geo_df = df.dropna(subset=['latitude', 'longitude'])

    if geo_df.empty:
        st.warning("Aucune donnée géolocalisée trouvée.")
        return

    map_center = [geo_df['latitude'].mean(), geo_df['longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=4)

    # Ajout de la HeatMap
    heat_data = geo_df[['latitude', 'longitude']].values.tolist()
    HeatMap(heat_data, radius=15).add_to(m)

    # Ajouter des marqueurs pour chaque crise
    df_points = geo_df.drop_duplicates(subset="topic")
    for _, row in df_points.iterrows():
        topic = row["topic"]
        crisis_df = geo_df[geo_df["topic"] == topic]
        n_tweets = len(crisis_df)
        n_positif = crisis_df[crisis_df["sentiment"] == "positive"].shape[0]
        p_positif = (n_positif / n_tweets) * 100 if n_tweets > 0 else 0
        exemple = crisis_df["text"].dropna().iloc[0][:100] + "..."
        popup_content = f"""
        <b>📌 Crise :</b> {topic}<br>
        <b>🔢 Tweets :</b> {n_tweets}<br>
        <b>🙂 % Positifs :</b> {p_positif:.1f}%<br>
        <b>💬 Exemple :</b> {exemple}
        """

        # Ici, on ajoute plus d'informations au tooltip
        tooltip_content = f"""
        <b>📌 Crise :</b> {topic}<br>
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=3,
            color="black",
            fill=True,
            fill_opacity=0.5,
            tooltip=folium.Tooltip(tooltip_content),  # Ajout d'informations supplémentaires au survol
            popup=folium.Popup(popup_content, max_width=300)
        ).add_to(m)

    # Affichage dans Streamlit
    st_folium(m, use_container_width=True, height=600)

def afficher_statistiques_temps(df):
    # --- 📈 Évolution des tweets dans le temps par topic ---

    # Vérifiez que les colonnes 'created_at' et 'topic' sont présentes
    if "created_at" in df.columns and "topic" in df.columns:
        df["date"] = df["created_at"].dt.date  # Extraire uniquement la date
        tweets_per_day_topic = df.groupby(["date", "topic"]).size().reset_index(name="Nombre_de_tweets")

        fig_time = px.line(
            tweets_per_day_topic,
            x="date",
            y="Nombre_de_tweets",
            color="topic",
            title="Évolution des tweets dans le temps par topic",
            labels={"date": "Date", "Nombre_de_tweets": "Nombre de Tweets", "topic": "Topic"},
            markers=True
        )
        fig_time.update_layout(title_x=0.5, xaxis_title="Date", yaxis_title="Nombre de Tweets")
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("Les colonnes 'created_at' ou 'topic' sont manquantes ou mal formatées.")

def afficherHashtag(dataframes):
    # Vérifie la présence du fichier nécessaire
    if "Hashtag_clean" not in dataframes:
        st.error("Le fichier 'Hashtag_clean.csv' est manquant dans le dossier CSV.")
        return

    df = dataframes["Hashtag_clean"]

    # Vérification des colonnes nécessaires
    required_columns = {"hashtag_id", "occurences"}
    if not required_columns.issubset(df.columns):
        st.error("Colonnes attendues manquantes dans le DataFrame.")
        return

    # Nettoyage des hashtags
    df['hashtag_id'] = df['hashtag_id'].astype(str).str.lower().str.strip()

    # Agrégation des occurrences
    top_hashtag_ids = df.groupby('hashtag_id')['occurences'].sum().reset_index()
    top_hashtag_ids = top_hashtag_ids.sort_values(by='occurences', ascending=False)

    # Slider interactif
    top_n = st.slider("Nombre de hashtags à afficher", min_value=5, max_value=30, value=10)

    # Affichage du graphique
    fig = px.bar(
        top_hashtag_ids.head(top_n),
        x='occurences',
        y='hashtag_id',
        orientation='h',
        title=f"Top {top_n} des hashtags les plus utilisés",
        labels={'occurences': 'Nombre d’occurrences', 'hashtag_id': 'Hashtag'}
    )

    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        title_x=0.5
    )

    st.plotly_chart(fig, use_container_width=True)
def afficher_repartition_par_topic(df):
    # --- 🥧 Répartition des tweets par topic ---
    st.subheader("📚 Répartition des tweets par topic")

    # Vérifier que la colonne 'topic' est présente
    if "topic" not in df.columns:
        st.warning("La colonne 'topic' est manquante dans le DataFrame.")
        return

    # Comptage des tweets par topic
    topic_counts = df["topic"].value_counts().reset_index()
    topic_counts.columns = ["Topic", "Nombre_de_tweets"]

    # --- 📊 Graphique Barres ---
    fig_topic_bar = px.bar(
        topic_counts,
        x="Topic",
        y="Nombre_de_tweets",
        text_auto=True,
        title="Répartition des tweets par topic",
        labels={"Topic": "Topic", "Nombre_de_tweets": "Nombre de Tweets"}
    )
    fig_topic_bar.update_layout(xaxis_tickangle=-45, title_x=0.5)
    st.plotly_chart(fig_topic_bar, use_container_width=True)

    # --- 🥧 Graphique Camembert ---
    fig_topic_pie = px.pie(
        topic_counts,
        values="Nombre_de_tweets",
        names="Topic",
        title="Répartition des tweets par topic",
        hole=0.4
    )
    fig_topic_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_topic_pie, use_container_width=True)