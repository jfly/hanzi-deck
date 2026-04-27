{ lib, inputs, ... }:
{
  imports = [
    ./uv2nix.nix
    inputs.devshell.flakeModule
  ];

  perSystem =
    { pkgs, ... }:
    let
      env = {
        MAKEMEAHANZI = toString inputs.makemeahanzi;
      };
    in
    {
      devshells.default.env = lib.attrsToList env;

      uv2nix = {
        python = pkgs.python314;

        workspaceRoot = ./..;

        pyprojectOverrides = final: prev: {
          hanzi-deck = prev.hanzi-deck.overrideAttrs (oldAttrs: {
            inherit env;
          });
        };
      };
    };
}
