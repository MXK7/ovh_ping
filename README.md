# OVH VPS Watch

Surveille le stock des VPS-2 OVHcloud (gammes 2026 et 2027) à Gravelines et Roubaix via l'API publique OVH, et alerte quand Linux repasse en stock.

Alertes : notification Windows + bip, et message Discord (optionnel).

## Utilisation

Windows uniquement (utilise `winsound`), Python 3, aucune dépendance.

```
copy .env.example .env   # puis remplir les valeurs
python ovh_vps_watch.py
```

## Configuration (`.env`)

| Variable | Rôle |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | Webhook Discord (optionnel, pas d'alerte Discord si absent) |
| `DISCORD_USER_ID` | ID Discord de l'utilisateur à mentionner (optionnel) |

Le fichier `.env` est ignoré par git.
