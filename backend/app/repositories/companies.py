from backend.app.models.entities import CompanyAnalytics
from backend.app.utils.context import track_db_time

class CompaniesRepository:
    ALLOWED_SORT_FIELDS = {
        "company", "total_jobs", "unique_locations", "avg_salary_min", 
        "avg_salary_max", "original_jobs_count", "highest_paying_role", 
        "latest_posting", "jobs_with_salary"
    }

    @classmethod
    @track_db_time
    def get_companies(
        cls, conn, limit: int, offset: int, sort_by: str, sort_order: str, 
        search: str | None, min_jobs: int | None
    ) -> tuple[list[CompanyAnalytics], int]:
        """
        Retrieves paginated, sorted, and filtered lists of companies, along with the total count.
        """
        # Validate sort parameters
        sort_col = sort_by.strip().lower()
        if sort_col not in cls.ALLOWED_SORT_FIELDS:
            sort_col = "company"
            
        order = sort_order.strip().upper()
        if order not in ("ASC", "DESC"):
            order = "ASC"

        # Build SQL dynamic conditions
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("company ILIKE %s")
            params.append(f"%{search}%")
            
        if min_jobs is not None:
            where_clauses.append("total_jobs >= %s")
            params.append(min_jobs)
            
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)

        # Count total records matching criteria
        count_query = f"SELECT COUNT(*) FROM serving.company_analytics {where_str};"
        
        # Query results
        query = f"""
            SELECT company, total_jobs, unique_locations, avg_salary_min, avg_salary_max,
                   original_jobs_count, highest_paying_role, latest_posting, jobs_with_salary,
                   created_at, updated_at
            FROM serving.company_analytics
            {where_str}
            ORDER BY {sort_col} {order}
            LIMIT %s OFFSET %s;
        """
        
        # Combine parameters
        query_params = list(params) + [limit, offset]
        
        with conn.cursor() as cursor:
            # 1. Get total records count
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            
            # 2. Get records
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            
            companies = [
                CompanyAnalytics(
                    company=row[0],
                    total_jobs=row[1],
                    unique_locations=row[2],
                    avg_salary_min=row[3],
                    avg_salary_max=row[4],
                    original_jobs_count=row[5],
                    highest_paying_role=row[6],
                    latest_posting=row[7],
                    jobs_with_salary=row[8],
                    created_at=row[9],
                    updated_at=row[10]
                )
                for row in rows
            ]
            
            return companies, total_records

    @staticmethod
    @track_db_time
    def get_company_by_name(conn, company_name: str) -> CompanyAnalytics | None:
        """
        Finds a single company by case-insensitive name match.
        """
        query = """
            SELECT company, total_jobs, unique_locations, avg_salary_min, avg_salary_max,
                   original_jobs_count, highest_paying_role, latest_posting, jobs_with_salary,
                   created_at, updated_at
            FROM serving.company_analytics
            WHERE LOWER(company) = LOWER(%s);
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (company_name,))
            row = cursor.fetchone()
            if not row:
                return None
            return CompanyAnalytics(
                company=row[0],
                total_jobs=row[1],
                unique_locations=row[2],
                avg_salary_min=row[3],
                avg_salary_max=row[4],
                original_jobs_count=row[5],
                highest_paying_role=row[6],
                latest_posting=row[7],
                jobs_with_salary=row[8],
                created_at=row[9],
                updated_at=row[10]
            )
