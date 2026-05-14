{ lib, ... }:
let
  fs = lib.fileset;
in
{
  perSystem =
    { pkgs, ... }:
    let
      inherit (pkgs) importNpmLock buildNpmPackage;
      nodejs = pkgs.nodejs_25; # Includes `Uint8Array.fromBase64`
    in
    {
      devShells.js = pkgs.mkShell {
        packages = [
          importNpmLock.hooks.linkNodeModulesHook
          nodejs
        ];

        npmDeps = importNpmLock.buildNodeModules {
          npmRoot = ./.;
          inherit nodejs;
        };
      };

      packages.js = buildNpmPackage (finalAttrs: {
        name = "hanzi-deck-writer";

        src = fs.toSource {
          root = ./.;
          fileset = fs.unions [
            ./src
            ./tsdown.config.ts
            ./package.json
            ./package-lock.json
          ];
        };

        npmDeps = importNpmLock { npmRoot = ./.; };

        npmConfigHook = importNpmLock.npmConfigHook;

        installPhase = ''
          mkdir $out
          mv dist/index.mjs $out/hanzi-deck-writer.js
        '';
      });
    };
}
