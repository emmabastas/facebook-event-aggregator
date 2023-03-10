{
  description = "";

  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        {
          devShells.default = pkgs.mkShell {
            packages = with pkgs; [
              (python3.withPackages (ps: with ps; [
                selenium

                # for the server
                flask
                gunicorn
              ]))
              chromium
              chromedriver

              # for the frontend
              nodejs
              nodePackages.typescript-language-server
            ];
          };
        }
      );
}
