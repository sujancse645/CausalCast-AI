#!/bin/bash
echo "Starting database restore..."
psql -U causalcast causalcast < /backup/causalcast_backup_.sql
echo "Restore complete."
