function buildToolbox(outdir)
    uuid = string(java.util.UUID.randomUUID());
    toolboxFolder = "./toolbox/";
    opts = matlab.addons.toolbox.ToolboxOptions(toolboxFolder, uuid);

    toolboxDirs = unique(fileparts(opts.ToolboxFiles));
    if ~all(contains(toolboxDirs, opts.ToolboxFolder))
        error("No symbolic links allowed in toolboxFolder (BUG through at least R2023a)");
    end

    opts.ToolboxName = "MRD";
    % TODO: Templatize ToolboxVersion
    opts.ToolboxVersion = "1.0.0";
    opts.OutputFile = fullfile(outdir, "mrd.mltbx");

    opts.Description = "Magnetic Resonance Data (MRD) toolbox for MATLAB";
    % opts.Summary = "";
    % opts.AuthorCompany = "";

    opts.MinimumMatlabRelease = "R2022b";

    % Must also specify which folders should be added to MATLAB path upon toolbox installation.
    % Must also include at least one *file* in the toolbox folder.
    % This seems to be bug on Linux, Matlab R2023a. On Windows, this isn't required.
    opts.ToolboxMatlabPath = toolboxFolder;

    matlab.addons.toolbox.packageToolbox(opts);
end
