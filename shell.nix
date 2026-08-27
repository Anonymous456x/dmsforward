{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.pip
    python311Packages.telegram-bot
    python311Packages.python-dotenv
    python311Packages.aiohttp
  ];
  
  shellHook = ''
    echo "✅ Python environment ready with all packages!"
    python --version
  '';
}
