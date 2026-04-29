{ lib, inputs, ... }:
{
  imports = [
    ./uv2nix.nix
    inputs.devshell.flakeModule
  ];

  perSystem =
    { config, pkgs, ... }:
    let
      python = pkgs.python314;
      env = {
        MAKEMEAHANZI = "${inputs.makemeahanzi}";
        HANZI_DECK_TEMPLATES = "${../templates}";
        HANZI_DECK_MEDIA = pkgs.linkFarm "media" [
          {
            # Note the underscore in the filename. That's necessary so anki actually
            # imports the media
            # https://docs.ankiweb.net/templates/fields.html#static-soundsimages
            name = "_hanzi-deck-writer.js";
            path = "${config.packages.js}/hanzi-deck-writer.js";
          }
        ];
      };
    in
    {
      devshells.default = {
        env = (lib.attrsToList env) ++ [
          {
            name = "HANZI_DECK_TEMPLATES";
            eval = "$PRJ_ROOT/templates";
          }
        ];
      };

      packages.default =
        pkgs.runCommand "hanzi.apkg"
          {
            inherit env;
          }
          ''
            mkdir $out
            ${lib.getExe' config.packages.hanzi-deck "hanzi-generate"} $out/hanzi.apkg
          '';

      uv2nix = {
        inherit python;

        workspaceRoot = ./..;

        pyprojectOverrides = final: prev: {
          hanzi-deck = prev.hanzi-deck.overrideAttrs (oldAttrs: {
            inherit env;
          });
        };
      };
    };
}
