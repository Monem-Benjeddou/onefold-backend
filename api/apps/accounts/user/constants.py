from django.utils.translation import gettext as _

"""

- **User** --> This is the primary end-user of the platform [1].
   --> This group includes **Fitness Enthusiasts** who are focused on advanced tracking of metrics like weight, macros, and workout logs [2] and are interested in social motivation through features like forums and achievements [2, 3]. 
   --> It also includes **Individuals managing Chronic Conditions** who utilize the platform to log symptoms and medications [1, 2]. Users interact with the platform by creating accounts [4, 5], logging various health and activity data [2, 4, 5], using health calculators [2, 6], engaging in the community forum by creating threads, posts, and comments [2-4, 7], earning points and badges [2, 4, 8, 9], and viewing their progress through analytics and reports [2, 5, 10]. 
   --> They can also leverage the AI features to generate meal or workout plans and interact with the AI chatbot [2, 11]. The user profile stores their health-specific attributes like age, weight, fitness level, and medical conditions [12-14].

- **Coach / Doctor** --> This role is outlined as a **planned future expansion** [2, 15, 16]. This category includes **Healthcare Providers** or coaches [1, 17] who could use the platform to monitor their clients or patients [2, 17]. The vision is for a dedicated portal [15] allowing them to review user logs [2, 17] and provide feedback [17]. 
   -->  These roles, such as "**coach**" or "**doctor**", would have **custom permissions** within the role-based authorization system [16, 18]. Future features could include telehealth capabilities like scheduling and video calls [15].

- **Admin** --> This role is for platform administrators [18, 19]. Admins have **full control** over the platform's management and content [19]. Their responsibilities include managing forum categories [7, 19], banning users [19], awarding points [19], and utilizing basic administrative tools [4]. This role typically corresponds to staff or superuser privileges [19] and requires robust security measures like 2FA [4, 18, 20] and strict access controls [21].

- **Moderator** --> This role is specifically for managing the **community forum** [19, 22, 23]. Moderators are responsible for overseeing forum content and user behavior within the community [19]. Their tasks include locking threads, pinning important posts, deleting offensive content, and handling user reports [19, 23-25]. This role would be assigned specific permissions, potentially via Django groups, to perform these moderation actions [19, 24].

- **Service** --> This is a non-human role representing **integrated systems** or **external tools** interacting with the platform's API [26]. These automated systems or third-party integrations use **API key authentication** [26, 27] for internal or microservice calls [26]. They require their own defined access levels within the authorization system [26].

```
- **User** --> This is the primary end-user of the platform, including **Fitness Enthusiasts** and **Individuals managing Chronic Conditions**. They are the core users who log data, use AI tools, and participate in the community.

    *   **Privileges/Permissions:**
        *   Can **create, read, update, and delete their own health data** (metrics, activities, symptoms, medications, meals).
        *   Can **view their own progress** and analytics dashboards.
        *   Can **use health calculators**.
        *   Can **generate AI-powered meal and workout plans**.
        *   Can **use the AI chatbot** for Q&A.
        *   Can **post threads, replies, and comments** in the community forum.
        *   Can **react to/like posts and comments**.
        *   Can **earn points and badges** for activities and achievements.
        *   Can **view leaderboards**.
        *   Can **update their own profile** details.
        *   Can **manage their settings** and notification preferences.
        *   Can **request export** of their own personal data (CSV, PDF).
        *   Can **request account deletion** (Right to Erasure).
        *   Can **accept/manage consent** for data processing/privacy policy.
        *   Can **block other users** (for social features).
        *   Access to their data is typically limited to themselves, unless explicitly authorized.

    *   **Specific Fields (on UserProfile or related models linked to User):**
        *   **UserProfile:** birthdate, sex, height, weight, fitness level, medical conditions (potentially encrypted), emergency contact (potentially encrypted), dietary preferences, restrictions. Also often stores calculated or summary data like current **points** or a flag for banning (`is_banned`).
        *   **UserBadge:** Links User to earned Badge instances.
        *   **PointsTransaction:** Logs individual point changes for the user.
        *   **Consent:** Records user's agreement to policies.
        *   **ActivityFeed/Activity:** Records events related to the user or their follows.

- **Coach / Doctor** --> This role is outlined as a **planned future expansion**. They are **Healthcare Providers** or coaches who could potentially monitor and guide users.

    *   **Privileges/Permissions:**
        *   Envisioned to have a portal to **review patient/client logs** and **provide feedback**. This implies a need for **access permissions to view specific users' data** (with the user's consent).
        *   Could potentially provide feedback **in the forum or via direct messaging**.
        *   Future integration could include **telehealth features** like scheduling and video calls.
        *   They would have **custom permissions** within the role-based authorization system.

    *   **Specific Fields (Potential, as this is future expansion):**
        *   Might have an extended profile model (`CoachProfile` or `ProviderProfile`) with professional details, credentials, specialization, and links to the users they are permitted to view.
        *   Relationship model linking `Coach/Doctor` user to multiple `User` accounts they are associated with, possibly with consent tracking for data sharing.

- **Admin** --> This role is for platform administrators. Admins have **full control** over the platform's management and content.

    *   **Privileges/Permissions:**
        *   Have **full control** over platform management.
        *   Can **manage forum categories** (create, update, delete).
        *   Can **ban or mute users**.
        *   Can **award points** to users.
        *   Can **utilize basic administrative tools**.
        *   Can **manage/review reports** from users about content/behavior.
        *   Can perform moderation actions on forum content (lock threads, pin posts, delete content).
        *   Have access to the **Django Admin panel**.
        *   Often associated with **staff or superuser** privileges.
        *   Sensitive access to user data (for support/audit) is logged.
        *   Requires **robust security measures** like 2FA.

    *   **Specific Fields (on User model, if they use standard Django Users):**
        *   `is_staff=True` and/or `is_superuser=True`.
        *   Potentially linked to specific Django Groups for permission management.

- **Moderator** --> This role is specifically for managing the **community forum**.

    *   **Privileges/Permissions:**
        *   Responsible for overseeing **forum content and user behavior** within the community.
        *   Can **lock threads**.
        *   Can **pin important posts**.
        *   Can **delete offensive content**.
        *   Can **handle user reports** on content or users.
        *   Can potentially **edit or remove user posts/comments**.
        *   Might **award certain badges** (like "Community Helper").
        *   These permissions would typically be assigned via **specific Django Groups** or custom permissions.

    *   **Specific Fields:**
        *   Assigned to a specific Django Group (e.g., "Moderator").

- **Service** --> This is a non-human role representing **integrated systems** or **external tools** interacting with the platform's API.

    *   **Privileges/Permissions:**
        *   Use **API key authentication** for internal or microservice calls and third-party integrations.
        *   Their permissions are **defined based on the service's function** (e.g., a service syncing data from a wearable device needs permission to create HealthMetric logs for a specific user; an AI service might need read access to profile data to generate a plan).
        *   Access levels are **defined within the authorization system**.

    *   **Specific Fields:**
        *   Might be represented by a model for **API Key management**, potentially linked to a "Service Account" or a representation of the integrating system, specifying its name, key, and granted permissions.

This structure covers the distinct capabilities and data associations for each role identified in the sources.
"""


ROLE_CHOICES = [
    ("user", _("User")),
    ("admin", _("Administrator")),
    ("moderator", _("Moderator")),
    ("service", _("Service")),
    # Removed manufacturer/collector/card_creator per requirements
]
