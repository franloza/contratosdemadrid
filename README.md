# Contratos de Madrid

This project provides scripts to download and process contract data from the Comunidad de Madrid public contracts portal.

You can view the live application at [contratosdemadrid.franloza.com](https://contratosdemadrid.franloza.com).

## Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repository-url>
    cd contratosdemadrid
    ```

2.  **Install dependencies and set up the environment:**
    This command will create a virtual environment, install Python packages, and download necessary browser binaries.
    ```bash
    make install
    ```

## Extract Data

Download contract data for a specified date range. Dates must be in `YYYY-MM-DD` format.
You can optionally specify a delay in seconds between downloads.

```bash
make extract START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD [DELAY_SECONDS=N]
```
**Example:**
```bash
make extract START_DATE=2023-01-01 END_DATE=2023-03-31 DELAY_SECONDS=5
```

## Transform Data

Process the extracted data to create refined data models.
```bash
make transform
```

## Init Application

The application is an Evidence project located in `src/app/`. To run it:

1.  **Navigate to the app directory:**
    ```bash
    cd src/app
    ```
2.  **Install npm dependencies:**
    ```bash
    npm install
    ```
3.  **Build data sources for Evidence:**
    ```bash
    npm run sources
    ```
4.  **Run the development server:**
    ```bash
    npm run dev
    ```
    Open your browser to the address indicated in the terminal (usually `http://localhost:3000`).
