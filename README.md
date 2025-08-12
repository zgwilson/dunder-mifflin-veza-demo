# Dunder Mifflin HRIS OAA Demo

This repository contains a demo application for Dunder Mifflin Paper Company using the Veza Open Authorization Architecture (OAA).

## Files Structure

- `application.json`: Application definition
- `identities.csv`: User identities (Michael, Jim, Pam, Dwight)
- `resources.csv`: Resources (branches, departments, paper types)
- `permissions.csv`: Permissions defined in the application
- `entitlements.csv`: Entitlements linking identities to permissions on resources
- `transform_data.py`: Script to generate OAA files

## How to Use

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/dunder-mifflin-oaa.git
   cd dunder-mifflin-oaa
