import typer

app = typer.Typer()


@app.command()
def main(name: str):
    print(f"hello, {name}")


if __name__ == "__main__":
    app()  # pragma: no cover
