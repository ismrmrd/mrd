function plan = buildfile
    import matlab.buildtool.tasks.CodeIssuesTask
    import matlab.buildtool.tasks.TestTask

    % Create a plan from task functions
    plan = buildplan(localfunctions);

    % Add a task to identify code issues
    plan("check") = CodeIssuesTask(Results="tests/results/static-analysis-results.sarif");

    % Add a task to run tests
    plan("test") = TestTask("tests", SourceFiles="toolbox", TestResults="tests/results/test-results.xml");

    % Make the "packageToolbox" task the default task in the plan
    plan.DefaultTasks = "packageToolbox";

    % Make the "packageToolbox" task dependent on the "check" and "test" tasks
    plan("packageToolbox").Dependencies = ["check" "test"];
end

function packageToolboxTask(~)
    buildToolbox("release");
end
