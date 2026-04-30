import marimo

__generated_with = "0.23.4"
app = marimo.App()


@app.cell
def _():
    import pandas as pd

    from hanzi_deck import hsk, subtlex

    hsk_data = hsk.load()
    freq_data = subtlex.load()

    df = pd.DataFrame(
        columns=["Character", "HSK 2026 Level", "Count per million characters"]
    )
    for char in set(hsk_data.keys()) & set(freq_data.keys()):
        hsk_datum = hsk_data[char]
        hsk_2026_level = hsk_datum.hsk_2026_level()
        if hsk_2026_level is None:
            continue

        freq_datum = freq_data[char]

        df.loc[len(df)] = [
            char,
            hsk_2026_level,
            freq_datum.character_count_per_million,
        ]

    df.plot.scatter(
        x="HSK 2026 Level",
        y="Count per million characters",
        title="Character frequency vs HSK level",
    )
    return (df,)


@app.cell
def _(df):
    df
    return


if __name__ == "__main__":
    app.run()
