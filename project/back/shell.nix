{
  pkgs ? import <nixpkgs> { },
}:

# Impure shell that lets uv manage the virtual environment
# This is simpler and more reliable for teaching environments
pkgs.mkShell {
  packages = [
    pkgs.python312
    pkgs.uv
  ];

  # Required for pyzmq and other packages with native dependencies
  buildInputs = [
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.zeromq
  ];

  shellHook = ''
    # Set LD_LIBRARY_PATH for native libraries
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.zeromq
    ]}:$LD_LIBRARY_PATH"
    
    echo "REMPY TP Development Environment"
    echo "================================="
    echo ""
    
    # Create and activate virtual environment if it doesn't exist
    if [ ! -d .venv ]; then
      echo "Creating virtual environment..."
      uv venv
    fi
    
    # Sync dependencies from pyproject.toml
    echo "Syncing dependencies..."
    uv sync
    
    # Activate the virtual environment
    source .venv/bin/activate
    
    echo ""
    echo "Virtual environment activated!"
    echo ""
    echo "To start Jupyter Notebook, run:"
    echo "  jupyter notebook"
    echo ""
    echo "Or for Jupyter Lab:"
    echo "  jupyter lab"
    echo ""
  '';
}
