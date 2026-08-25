# MRD Viz researcher release bundle install

This bundle contains:

1. `mrd-viz-<version>.vsix` (VS Code extension)
2. `mrd_viz-<version>-py3-none-any.whl` (backend wheel)
3. `mrd-viz-<version>.tar.gz` (backend source distribution fallback)

## Quick install

1. Install the extension:

   ```bash
   code --install-extension mrd-viz-<version>.vsix
   ```

2. In VS Code, run **MRD Viz: Set Up Backend**.
3. Choose **Install backend from local wheel**.
4. Select the `mrd_viz-*.whl` file from this bundle.
5. Re-open your `.mrd` file.

If the wheel install is blocked by local policy, use **Set Up Backend** with the managed auto-install option, or manually select a pre-provisioned interpreter via **MRD Viz: Select Python Interpreter**.
