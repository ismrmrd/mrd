function plan = buildfile
    import matlab.buildtool.tasks.CodeIssuesTask
    import matlab.buildtool.tasks.TestTask

    plan = buildplan(localfunctions);
    plan("check") = CodeIssuesTask(Results="tests/results/static-analysis-results.sarif");
    plan("test") = TestTask("tests", SourceFiles="toolbox", TestResults="tests/results/test-results.xml");

    plan.DefaultTasks = ["check", "test"];

    % Make the "packageToolbox" task dependent on the "check" and "test" tasks
    % plan("packageToolbox").Dependencies = ["check" "test"];
end

function packageToolboxTask(~)
    buildToolbox("release");
end
