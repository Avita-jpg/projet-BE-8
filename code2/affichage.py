import streamlit as st
import variables
import general
import pandas as pd
import sentiment
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import gravite
import aide
import variables
import interactions
import categorie

def accueil():
    st.title("Bienvenue sur le Tableau de bord des Tweets 📈")
    st.markdown(
        """
        Ce tableau de bord interactif vous permet d’explorer et d’analyser des données issues de Twitter en contexte de crise.  
        
        Utilisez le menu à gauche pour :
        - Voir des statistiques globales sur les tweets
        - Faire des recherches personnalisees
        - Visualiser l’évolution des tweets dans le temps
        - Découvrir les hashtags les plus utilisés
        - Comparer des crises entre elles
        - Suivre une crise en particulier
        - Gravité
        - Demande d'aide
        - Top influenceur
        - Analyser les utilisateurs, les catégories, la localisation, etc.
        """
    )
def vueEnsemble(dataframes):
    labels = variables.getTrecisCrises(dataframes)
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
        general.afficher_statistiques_temps(df)
    with col3:
        general.create_heatmap(df)
    with col4: 
        general.afficherHashtag(df, readable_topics=variables.getTrecisCrises(dataframes))
    general.afficher_repartition_par_topic(df)


def suiviCrise(data):
    
    st.title("🔎 Analyse et suivi d'une crise : Volume & Sentiments")

    selected_label=st.selectbox("Crises",variables.getCrises(data))
    df= data["Tweet_sentiment_localisation"]
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df_crisis= df[(df["topic"]==variables.getCrisesTrecis(data)[selected_label])]
    merged = variables.getMergedDemandeDaide(data)
    merged = merged[merged['event_id'] == selected_label]
    expanderGeneral=st.expander("General",expanded=True)
    with expanderGeneral:
        st.markdown(f"- **Nombre de tweets** : {len(df_crisis)}")
        dernier_tweet = df_crisis["created_at"].max()
        if pd.notnull(dernier_tweet):
            st.markdown(f"- **Dernier tweet** : {dernier_tweet.strftime('%Y-%m-%d %H:%M')}")
        col1,col2=st.columns([4,3])
        with col1:
            general.afficherTimeline(merged)
        with col2:
            general.afficherLocalisation(df_crisis)
    expanderSentiment= st.expander("Sentiment",expanded=True)
    with expanderSentiment:
        sentiment.repartitionSentiment(df_crisis)
        df_event = data["tweets_par_event"]
        eventids = sorted(df_event['crise_id'].astype(str).unique())
        df_selected = df_event[df_event['crise_id'].astype(str) == selected_label]
    expanderWordcloud= st.expander("Wordcloud mot revenant le plus")
    with expanderWordcloud:
        gravite.afficher_wordcloud_gravite(df_selected)
    expanderGravite = st.expander("Gravité",expanded=True)
    with expanderGravite:
        gravite.afficher_gravite_event_plotly(df_selected,selected_label)
        gravite.afficher_tweets_gravite(df_selected)
    
    expanderHelp=st.expander("Demande d'aide",expanded=True)
    with expanderHelp:        
        aide.getInfosAide(merged)
        aide.getRepartitionTypeDemande(merged)
        
    expanderInfluenceur= st.expander("Influenceurs",expanded=True)
    with expanderInfluenceur:
        general.afficherInfluenceur(data,selected_label)
    expanderCategorie= st.expander("Catégories des posts",expanded=True)
    with expanderCategorie: 
        categorie.afficher_repartition_categories_crise(df_crisis, variables.getCrisesTrecis(data)[selected_label], readable_topics=variables.getTrecisCrises(data))
    expanderHashtag=st.expander("Hashtags",expanded=True)
    with expanderHashtag:
        general.afficherTopHashtagParCriseFromList(df_crisis, variables.getCrisesTrecis(data)[selected_label],readable_topics=variables.getTrecisCrises(data))

    

def recherchePersonalisee(dataframes):

    labels = variables.getTrecisCrises(dataframes)

    st.title("🔎 Recherche personnalisée dans les tweets")

    if "Tweet_sentiment_localisation" not in dataframes:
        st.error("Le fichier 'Tweet_sentiment_localisation.csv' est manquant.")
        return

    df = dataframes["Tweet_sentiment_localisation"].copy()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["topic"] = df["topic"].map(labels).fillna(df["topic"])

    st.markdown("Filtre les tweets selon tes propres critères 👇")

    # 🔤 Filtrage par mot-clé
    keyword = st.text_input("🔤 Contient le mot-clé :")
    if keyword:
        df = df[df["text"].str.contains(keyword, case=False, na=False)]

    # 📅 Filtrage par date
    min_date = df["created_at"].min().date()
    max_date = df["created_at"].max().date()
    date_range = st.slider("📅 Plage de dates :", min_value=min_date, max_value=max_date,
                           value=(min_date, max_date))
    df = df[(df["created_at"].dt.date >= date_range[0]) & (df["created_at"].dt.date <= date_range[1])]

    # 📍 Filtrage par lieu
    lieux = df["lieu_extrait"].dropna().unique()
    lieux_selectionnes = st.multiselect("📍 Lieu :", options=sorted(lieux))
    if lieux_selectionnes:
        df = df[df["lieu_extrait"].isin(lieux_selectionnes)]

    # 🎭 Filtrage par sentiment
    sentiments =["Tous","Positif","Neutre","Negatif"]
    sentMap={"Positif":"positive","Negatif":"negative","Neutre":"neutral"}
    
    #sentiments_selectionnes = st.multiselect("🎭 Sentiment :", options=sorted(sentiments))
    sentiments_selectionnes= st.pills("🎭 Sentiment :",options=sentiments,selection_mode="single",default="Tous")
    if sentiments_selectionnes!="Tous":
        df = df[df["sentiment"].isin([sentMap[sentiments_selectionnes]])]

    # 📄 Affichage des résultats
    st.markdown(f"📄 **{len(df)} tweets** trouvés avec ces filtres.")
    st.dataframe(
        df[["created_at", "text", "sentiment", "lieu_extrait", "topic"]]
        .sort_values("created_at", ascending=False),
        use_container_width=True
    )

    # ⬇️ Export CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Télécharger les résultats", data=csv, file_name="tweets_filtrés.csv", mime="text/csv")

def comparateurCrises(dataframes):
    labels = variables.getTrecisCrises(dataframes)

    st.title("⚖️ Comparateur de crises – Statistiques globales")

    if "Tweet_sentiment_localisation" not in dataframes:
        st.error("Le fichier 'Tweet_sentiment_localisation.csv' est manquant.")
        return

    df = dataframes["Tweet_sentiment_localisation"]

    required_cols = {"tweet_id", "topic", "retweet_count", "favorite_count"}
    if not required_cols.issubset(df.columns):
        st.error("Colonnes nécessaires manquantes.")
        return

    # Liste des topics lisibles
    topics = df["topic"].dropna().unique()
    readable_topics = {topic: labels.get(topic, topic) for topic in topics}

    selected_labels = st.multiselect(
        "📌 Sélectionnez les crises à comparer",
        options=[readable_topics[t] for t in sorted(topics)],
        default=[readable_topics[t] for t in sorted(topics)[:2]]
    )

    label_to_code = {v: k for k, v in readable_topics.items()}
    selected_codes = [label_to_code[label] for label in selected_labels if label in label_to_code]

    if not selected_codes:
        st.warning("Veuillez choisir au moins une crise.")
        return

    df_filtered = df[df["topic"].isin(selected_codes)]

    stats = df_filtered.groupby("topic").agg(
        Nombre_de_tweets=("tweet_id", "count"),
        Total_retweets=("retweet_count", "sum"),
        Moyenne_likes=("favorite_count", "mean")
    ).reset_index()

    stats["Moyenne_likes"] = stats["Moyenne_likes"].round(2)
    stats["topic"] = stats["topic"].map(readable_topics)

    # --- 📋 Tableau Résumé ---
    st.subheader("📋 Statistiques comparées")
    st.dataframe(stats, use_container_width=True)

    # --- 📊 Barres groupées : Tweets + Retweets ---
    st.subheader("📈 Comparaison du nombre de tweets et de retweets")
    stats_bar = stats.melt(id_vars="topic", value_vars=["Nombre_de_tweets", "Total_retweets"],
                           var_name="Indicateur", value_name="Valeur")

    fig_bar = px.bar(
        stats_bar,
        x="topic",
        y="Valeur",
        color="Indicateur",
        barmode="group",
        text_auto=True,
        title="Comparaison entre Nombre de Tweets et Total de Retweets"
    )
    fig_bar.update_layout(xaxis_tickangle=-45, title_x=0.5)
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 💬 Barres Moyenne de Likes ---
    st.subheader("👍 Comparaison de la moyenne des likes par tweet")
    fig_likes = px.bar(
        stats,
        x="topic",
        y="Moyenne_likes",
        color_discrete_sequence=["#FF69B4"],  # rose stylé
        text_auto=True,
        title="Moyenne de likes par tweet pour chaque crise"
    )
    fig_likes.update_layout(xaxis_tickangle=-45, title_x=0.5)
    st.plotly_chart(fig_likes, use_container_width=True)

    # --- 🥧 Camembert Répartition Tweets ---
    st.subheader("🥧 Répartition du volume de tweets")
    fig_pie = px.pie(
        stats,
        values="Nombre_de_tweets",
        names="topic",
        title="Part relative du nombre de tweets",
        hole=0.4
    )
    fig_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- 📈 Répartition du sentiment par crise ---
    st.subheader("💬 Répartition du sentiment par crise")
    sentiment_counts = df_filtered.groupby(["topic", "sentiment"]).size().reset_index(name="count")
    sentiment_counts["topic"] = sentiment_counts["topic"].map(readable_topics)

    fig_sentiment = px.bar(
        sentiment_counts,
        x="sentiment",
        y="count",
        color="topic",
        barmode="group",
        text_auto=True,
        title="Répartition des sentiments par crise",
        labels={"sentiment": "Sentiment", "count": "Nombre de Tweets"}
    )
    fig_sentiment.update_layout(xaxis_tickangle=-45, title_x=0.5)
    st.plotly_chart(fig_sentiment, use_container_width=True)
    categorie.afficher_comparaison_categories_crises(df_filtered, readable_topics=readable_topics)

def interaction_page(dataframes):
    #TODO 
    data=interactions.load_data_interaction(dataframes)
    crises = list(data.keys())
    selected_crisis = st.selectbox("Sélectionnez une crise", crises)
    sample_size = st.slider("Taille de l'échantillon de tweets à afficher", min_value=50, max_value=1000, value=200, step=50)
    event_df = data[selected_crisis]
    st.subheader(f"Graphe d'interactions pour la crise : {selected_crisis.capitalize()}")
    G = interactions.create_graph(event_df, sample_size)
    # Affichage du graphe ou message si vide
    if G.number_of_nodes() == 0:
        st.warning("Aucun graphe à afficher pour cette crise.")
    else:
        interactions.draw_graph(G)

        # Affichage des utilisateurs les plus actifs
        st.subheader("Utilisateurs les plus actifs dans ce graphe")
        top_users_df = interactions.get_most_active_users(G, pd.read_csv("../CSV/User_clean.csv"))
        st.dataframe(top_users_df)



def carteGlobale(dataframes):
    labels = variables.getTrecisCrises(dataframes)

    st.title("🧭 Carte des Tweets géolocalisés")

    if "Tweet_sentiment_localisation" not in dataframes:
        st.error("Tweet_sentiment_localisation est manquant.")
        return

    df = dataframes["Tweet_sentiment_localisation"]

    required_cols = {"latitude", "longitude", "retweet_count", "sentiment", "text", "topic"}
    if not required_cols.issubset(df.columns):
        st.error("Colonnes nécessaires manquantes.")
        return

    df_geo = df.dropna(subset=["latitude", "longitude", "retweet_count", "sentiment", "text"])
    df_geo = df_geo[(df_geo["latitude"] != 0) & (df_geo["longitude"] != 0)]

    if df_geo.empty:
        st.warning("Aucun tweet géolocalisé trouvé.")
        return

    # Mapping inverse
    label_to_code = {v: k for k, v in labels.items()}

    crises_codes = df_geo["topic"].dropna().unique()
    crises_lisibles = [labels.get(code, code) for code in sorted(crises_codes)]

    selected_label = st.selectbox("📌 Filtrer par crise (facultatif)", options=["Toutes"] + crises_lisibles)

    if selected_label != "Toutes":
        selected_code = label_to_code.get(selected_label, selected_label)
        df_geo = df_geo[df_geo["topic"] == selected_code]

    if df_geo.empty:
        st.warning("Aucun tweet trouvé pour cette crise.")
        return

    # Filtrer par nombre minimal de retweets
    min_retweet, max_retweet = int(df_geo["retweet_count"].min()), int(df_geo["retweet_count"].max())
    seuil_retweet = st.slider("🎚️ Nombre minimal de retweets à afficher :", min_value=min_retweet,
                              max_value=max_retweet, value=min_retweet, step=1)

    df_geo = df_geo[df_geo["retweet_count"] >= seuil_retweet]

    if df_geo.empty:
        st.warning("Aucun tweet ne correspond au seuil de retweets.")
        return

    # Ajouter un jitter pour éviter le chevauchement
    np.random.seed(42)
    df_geo["latitude_jitter"] = df_geo["latitude"] + np.random.uniform(-0.01, 0.01, size=len(df_geo))
    df_geo["longitude_jitter"] = df_geo["longitude"] + np.random.uniform(-0.01, 0.01, size=len(df_geo))

    df_geo["taille_point"] = df_geo["retweet_count"].apply(lambda x: max(5, min(x * 0.5, 40)))

    # Choix de la vue : Points ou Heatmap pondérée
    vue = st.radio("🗺️ Choisir la vue :", [
        "📍 Carte des tweets (points)",
        "🔥 Heatmap pondérée (par retweets)"
    ])

    if vue == "📍 Carte des tweets (points)":
        st.markdown("**🧭 Chaque point = un tweet | Taille = nombre de retweets | Couleur = sentiment**")
        fig = px.scatter_mapbox(
            df_geo,
            lat="latitude",
            lon="longitude",
            hover_name="text",
            hover_data={"retweet_count": True, "sentiment": True},
            size="taille_point",
            color="sentiment",
            color_discrete_map={
                "positive": "green",
                "neutral": "gray",
                "negative": "red"
            },
            zoom=2,
            height=700
        )

    elif vue == "🔥 Heatmap pondérée (par retweets)":
        st.markdown("**🔸 Plus c'est chaud, plus la crise est retweetée dans la zone.**")
        fig = go.Figure()
        fig.add_trace(go.Densitymapbox(
            lat=df_geo["latitude_jitter"],
            lon=df_geo["longitude_jitter"],
            z=df_geo["retweet_count"],
            radius=30,
            colorscale="YlGnBu",
            showscale=True,
            hoverinfo='skip'
        ))

    # Layout final
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=2,
            center=dict(
                lat=df_geo["latitude"].mean(),
                lon=df_geo["longitude"].mean()
            )
        ),
        height=700,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    st.plotly_chart(fig, use_container_width=True)