function plan = buildfile
    import matlab.buildtool.tasks.CodeIssuesTask
    import matlab.buildtool.tasks.TestTask

    plan = buildplan(localfunctions);
    plan("check") = CodeIssuesTask(Results="tests/results/static-analysis-results.sarif");
    plan("test") = TestTask("tests", SourceFiles="toolbox", TestResults="tests/results/test-results.xml");

    plan("packageToolbox").Dependencies = ["check" "test"];

    plan.DefaultTasks = ["packageToolbox"];
end

function packageToolboxTask(~)
    buildToolbox("release");
end
