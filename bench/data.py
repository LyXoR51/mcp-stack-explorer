TABLES = {
    "clientele": [
        {"id": 1, "nom": "Camille Roux", "ville": "Rivebourg", "inscrit_le": "2023-03-14"},
        {"id": 2, "nom": "Théo Vasseur", "ville": "Valmont", "inscrit_le": "2023-09-02"},
        {"id": 3, "nom": "Inès Marchand", "ville": "Rivebourg", "inscrit_le": "2024-01-20"},
        {"id": 4, "nom": "Malo Girard", "ville": "Valmont", "inscrit_le": "2024-05-07"},
    ],
    "pieces_stock": [
        {"id": 1, "reference": "PX-100", "designation": "Chaîne 9 vitesses", "prix_eur": 18.50, "quantite": 12},
        {"id": 2, "reference": "PX-101", "designation": "Plaquettes de frein", "prix_eur": 9.90, "quantite": 30},
        {"id": 3, "reference": "PX-102", "designation": "Pneu 700x28", "prix_eur": 24.00, "quantite": 8},
        {"id": 4, "reference": "PX-103", "designation": "Dérailleur arrière", "prix_eur": 54.90, "quantite": 3},
        {"id": 5, "reference": "PX-104", "designation": "Selle route", "prix_eur": 39.00, "quantite": 0},
    ],
    "interventions": [
        {"id": 1, "client_id": 2, "piece_ref": "PX-101", "type": "révision", "statut": "terminée", "cout_eur": 45.00},
        {"id": 2, "client_id": 1, "piece_ref": "PX-100", "type": "remplacement chaîne", "statut": "terminée", "cout_eur": 35.00},
        {"id": 3, "client_id": 4, "piece_ref": "PX-102", "type": "crevaison", "statut": "terminée", "cout_eur": 15.00},
        {"id": 4, "client_id": 3, "piece_ref": "PX-103", "type": "remplacement dérailleur", "statut": "en cours", "cout_eur": 89.90},
        {"id": 5, "client_id": 2, "piece_ref": "PX-104", "type": "remplacement selle", "statut": "en attente", "cout_eur": 52.00},
    ],
}