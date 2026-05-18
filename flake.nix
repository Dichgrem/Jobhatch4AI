{
  description = "Jobhatch4AI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312.withPackages (ps: with ps; [
          fastapi
          uvicorn
          pydantic
          openai
          pytest
          httpx
          jieba
          numpy
          pandas
          torch
          python-multipart
          python-dotenv
          scikit-learn
        ]);
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.bun
          ];
        };
      }
    );
}
