package br.com.talentflow.core

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class User(
    val id: Int, val name: String, val email: String, val role: String,
    @SerialName("company_id") val companyId: Int, val company: String = "",
)

@Serializable
data class Job(
    val id: Int, val code: String, val title: String,
    val department: String = "", val location: String = "", val modality: String = "", val seniority: String = "",
    val description: String = "", val requirements: String = "",
    val status: String = "open", @SerialName("due_date") val dueDate: String = "",
    val applications: Int = 0, val version: Int = 1,
)

@Serializable
data class Stage(val id: Int, val name: String, val kind: String = "active", val order: Int = 0)

@Serializable
data class Candidate(
    val id: Int, val name: String, val email: String = "", val phone: String = "", val location: String = "",
    val title: String = "", val source: String = "", val skills: String = "",
    @SerialName("experience_years") val experienceYears: Int = 0, val education: String = "",
)

@Serializable
data class ApplicationRow(
    val id: Int, @SerialName("candidate_id") val candidateId: Int, @SerialName("job_id") val jobId: Int,
    @SerialName("stage_id") val stageId: Int, val stage: String = "", val status: String = "active",
    val fit: Int = 0, val version: Int = 1, val candidate: Candidate,
)

@Serializable
data class JobDetail(val job: Job, val stages: List<Stage>, val applications: List<ApplicationRow>)

@Serializable
data class DashboardMetrics(
    @SerialName("jobs_open") val jobsOpen: Int = 0, @SerialName("jobs_approval") val jobsApproval: Int = 0,
    @SerialName("candidates_active") val candidatesActive: Int = 0, val hired: Int = 0, val rejected: Int = 0,
    val interviews: Int = 0, @SerialName("avg_time_hire") val avgTimeHire: Double = 0.0, val conversion: Double = 0.0,
    @SerialName("pending_tasks") val pendingTasks: Int = 0, @SerialName("late_jobs") val lateJobs: Int = 0,
)

@Serializable
data class NamedCount(val name: String, val value: Int)

@Serializable
data class Dashboard(val metrics: DashboardMetrics, val stages: List<NamedCount> = emptyList())

@Serializable
data class Employee(
    val id: Int, val name: String, @SerialName("employee_code") val employeeCode: String = "",
    val department: String = "", @SerialName("job_title") val jobTitle: String = "",
    @SerialName("hire_date") val hireDate: String = "", val status: String = "active",
)

@Serializable
data class PlanAction(val title: String, val done: Boolean = false, val evidence: String = "")

@Serializable
data class Plan(
    val id: Int, @SerialName("employee_id") val employeeId: Int, val employee: String = "", val title: String,
    val competency: String = "", val actions: List<PlanAction> = emptyList(), val progress: Int = 0,
    val status: String = "active", @SerialName("due_date") val dueDate: String = "", val version: Int = 1,
)

@Serializable
data class Leave(
    val id: Int, @SerialName("employee_id") val employeeId: Int, val employee: String = "", val department: String = "",
    val kind: String = "vacation", @SerialName("starts_on") val startsOn: String, @SerialName("ends_on") val endsOn: String,
    val days: Int = 0, val status: String = "pending",
)

@Serializable
data class Insights(
    val population: Int = 0, val active: Int = 0, @SerialName("pending_leaves") val pendingLeaves: Int = 0,
    @SerialName("plan_count") val planCount: Int = 0, @SerialName("completed_plans") val completedPlans: Int = 0,
)

@Serializable
data class PortalInterview(val id: Int, @SerialName("starts_at") val startsAt: String, val status: String = "")

@Serializable
data class PortalApplication(
    val id: Int, val job: String, val company: String = "", val stage: String, val status: String = "",
    @SerialName("applied_at") val appliedAt: String = "", val interviews: List<PortalInterview> = emptyList(),
)

@Serializable
data class Portal(val applications: List<PortalApplication> = emptyList())

@Serializable
data class SessionInfo(val id: String, val client: String, val kind: String = "", val current: Boolean = false)

@Serializable
data class HealthInfo(
    @SerialName("api_version") val apiVersion: String,
    @SerialName("min_client_version") val minClientVersion: Map<String, String> = emptyMap(),
)

@Serializable
data class ChangeItem(val seq: Long, val entity: String, val action: String = "")

@Serializable
data class Changes(val cursor: Long, val latest: Long = 0, @SerialName("has_more") val hasMore: Boolean = false,
                   val entities: List<String> = emptyList(), val items: List<ChangeItem> = emptyList())

@Serializable
data class Cursor(val cursor: Long)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String, @SerialName("refresh_token") val refreshToken: String,
    @SerialName("expires_in") val expiresIn: Int = 900, val user: User,
)

@Serializable
data class RefreshResponse(
    @SerialName("access_token") val accessToken: String, @SerialName("refresh_token") val refreshToken: String,
)

@Serializable
data class MeEnvelope(val user: User)

@Serializable
data class MoveResult(val ok: Boolean = true, val stage: String = "", val status: String = "", val version: Int = 0)

/** Compara versões "1.3.0-rc.1" ignorando sufixos; usado para avisar que o app está abaixo do mínimo da API. */
fun isVersionBelow(current: String, minimum: String): Boolean {
    fun parts(v: String) = v.substringBefore('-').split('.').map { it.toIntOrNull() ?: 0 }
    val a = parts(current); val b = parts(minimum)
    for (i in 0 until maxOf(a.size, b.size)) {
        val x = a.getOrElse(i) { 0 }; val y = b.getOrElse(i) { 0 }
        if (x != y) return x < y
    }
    return false
}
