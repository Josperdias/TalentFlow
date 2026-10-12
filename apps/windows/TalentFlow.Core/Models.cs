using System.Text.Json.Serialization;

namespace TalentFlow.Core;

public sealed record User(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("email")] string Email,
    [property: JsonPropertyName("role")] string Role,
    [property: JsonPropertyName("company_id")] int CompanyId,
    [property: JsonPropertyName("company")] string Company = "");

public sealed record Job(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("code")] string Code,
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("department")] string Department = "",
    [property: JsonPropertyName("location")] string Location = "",
    [property: JsonPropertyName("modality")] string Modality = "",
    [property: JsonPropertyName("status")] string Status = "open",
    [property: JsonPropertyName("due_date")] string DueDate = "",
    [property: JsonPropertyName("applications")] int Applications = 0,
    [property: JsonPropertyName("version")] int Version = 1);

public sealed record Stage(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("kind")] string Kind = "active");

public sealed record Candidate(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("email")] string Email = "",
    [property: JsonPropertyName("title")] string Title = "",
    [property: JsonPropertyName("location")] string Location = "",
    [property: JsonPropertyName("source")] string Source = "",
    [property: JsonPropertyName("skills")] string Skills = "",
    [property: JsonPropertyName("experience_years")] int ExperienceYears = 0);

public sealed record ApplicationRow(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("job_id")] int JobId,
    [property: JsonPropertyName("stage_id")] int StageId,
    [property: JsonPropertyName("stage")] string Stage,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("fit")] int Fit,
    [property: JsonPropertyName("version")] int Version,
    [property: JsonPropertyName("candidate")] Candidate Candidate);

public sealed record JobDetail(
    [property: JsonPropertyName("job")] Job Job,
    [property: JsonPropertyName("stages")] List<Stage> Stages,
    [property: JsonPropertyName("applications")] List<ApplicationRow> Applications);

public sealed record DashboardMetrics(
    [property: JsonPropertyName("jobs_open")] int JobsOpen = 0,
    [property: JsonPropertyName("jobs_approval")] int JobsApproval = 0,
    [property: JsonPropertyName("candidates_active")] int CandidatesActive = 0,
    [property: JsonPropertyName("hired")] int Hired = 0,
    [property: JsonPropertyName("rejected")] int Rejected = 0,
    [property: JsonPropertyName("interviews")] int Interviews = 0,
    [property: JsonPropertyName("avg_time_hire")] double AvgTimeHire = 0,
    [property: JsonPropertyName("conversion")] double Conversion = 0);

public sealed record NamedCount(
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("value")] int Value);

public sealed record Dashboard(
    [property: JsonPropertyName("metrics")] DashboardMetrics Metrics,
    [property: JsonPropertyName("stages")] List<NamedCount> Stages);

public sealed record TrendPoint(
    [property: JsonPropertyName("month")] string Month,
    [property: JsonPropertyName("applications")] int Applications = 0,
    [property: JsonPropertyName("hired")] int Hired = 0);

public sealed record Trend(
    [property: JsonPropertyName("points")] List<TrendPoint> Points,
    [property: JsonPropertyName("total_applications")] int TotalApplications = 0,
    [property: JsonPropertyName("total_hired")] int TotalHired = 0,
    [property: JsonPropertyName("note")] string Note = "");

public sealed record Employee(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("employee_code")] string EmployeeCode = "",
    [property: JsonPropertyName("department")] string Department = "",
    [property: JsonPropertyName("job_title")] string JobTitle = "",
    [property: JsonPropertyName("status")] string Status = "active");

public sealed record PlanAction(
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("done")] bool Done = false,
    [property: JsonPropertyName("evidence")] string Evidence = "");

public sealed record Plan(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("employee")] string Employee,
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("actions")] List<PlanAction> Actions,
    [property: JsonPropertyName("progress")] int Progress,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("due_date")] string DueDate,
    [property: JsonPropertyName("version")] int Version);

public sealed record Leave(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("employee")] string Employee,
    [property: JsonPropertyName("kind")] string Kind,
    [property: JsonPropertyName("starts_on")] string StartsOn,
    [property: JsonPropertyName("ends_on")] string EndsOn,
    [property: JsonPropertyName("days")] int Days,
    [property: JsonPropertyName("status")] string Status);

public sealed record Insights(
    [property: JsonPropertyName("population")] int Population = 0,
    [property: JsonPropertyName("active")] int Active = 0,
    [property: JsonPropertyName("pending_leaves")] int PendingLeaves = 0,
    [property: JsonPropertyName("plan_count")] int PlanCount = 0,
    [property: JsonPropertyName("completed_plans")] int CompletedPlans = 0);

public sealed record PortalInterview([property: JsonPropertyName("starts_at")] string StartsAt);

public sealed record PortalApplication(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("job")] string Job,
    [property: JsonPropertyName("company")] string Company,
    [property: JsonPropertyName("stage")] string Stage,
    [property: JsonPropertyName("interviews")] List<PortalInterview> Interviews);

public sealed record Portal([property: JsonPropertyName("applications")] List<PortalApplication> Applications);

public sealed record SessionInfo(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("client")] string Client,
    [property: JsonPropertyName("kind")] string Kind,
    [property: JsonPropertyName("current")] bool Current);

public sealed record HealthInfo(
    [property: JsonPropertyName("api_version")] string ApiVersion,
    [property: JsonPropertyName("min_client_version")] Dictionary<string, string>? MinClientVersion);

public sealed record Changes(
    [property: JsonPropertyName("cursor")] long Cursor,
    [property: JsonPropertyName("has_more")] bool HasMore,
    [property: JsonPropertyName("entities")] List<string> Entities);

public sealed record CursorResponse([property: JsonPropertyName("cursor")] long Cursor);

public sealed record TokenResponse(
    [property: JsonPropertyName("access_token")] string AccessToken,
    [property: JsonPropertyName("refresh_token")] string RefreshToken,
    [property: JsonPropertyName("user")] User User);

public sealed record RefreshResponse(
    [property: JsonPropertyName("access_token")] string AccessToken,
    [property: JsonPropertyName("refresh_token")] string RefreshToken);

public sealed record MoveResult(
    [property: JsonPropertyName("stage")] string Stage = "",
    [property: JsonPropertyName("version")] int Version = 0);

public sealed record MeEnvelope([property: JsonPropertyName("user")] User User);
public sealed record RevokeResult([property: JsonPropertyName("revoked")] int Revoked);

public static class Versions
{
    /// <summary>"1.3.0-rc.1" &lt; "1.3.0"? Compara só major.minor.patch (ignora sufixo).</summary>
    public static bool IsBelow(string current, string minimum)
    {
        static int[] Parse(string v) => v.Split('-')[0].Split('.').Select(p => int.TryParse(p, out var n) ? n : 0).ToArray();
        var a = Parse(current); var b = Parse(minimum);
        for (var i = 0; i < Math.Max(a.Length, b.Length); i++)
        {
            var x = i < a.Length ? a[i] : 0; var y = i < b.Length ? b[i] : 0;
            if (x != y) return x < y;
        }
        return false;
    }
}
