#!/bin/bash
echo "Starting database backup..."
pg_dump -U causalcast causalcast > /backup/causalcast_backup_$(date +%F).sql
echo "Backup complete."
