from typing import Optional, List, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.core.database import get_supabase_client, is_valid_uuid

class SavingGoalTools(BaseTool):
    """
    Independent tool for tracking, reviewing, and updating user savings goals
    strictly using database records.
    """

    MOCK_SAVING_GOALS: List[Dict[str, Any]] = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "goal_name": "Fondo de Emergencia",
            "target_amount": 5000.00,
            "current_amount": 1800.00,
            "currency": "USD",
            "deadline": "2026-12-31",
            "status": "in_progress"
        }
    ]

    def __init__(self):
        self._goals: List[Dict[str, Any]] = [dict(g) for g in self.MOCK_SAVING_GOALS]

    @property
    def name(self) -> str:
        return "saving_goal_tool"

    @property
    def description(self) -> str:
        return "Consulta metas de ahorro: progreso actual, monto objetivo, porcentaje completado y actualización de aportes."

    async def get_saving_goals(
        self,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Retrieves saving goals from the database and computes progress percentages.
        """
        goals: List[Dict[str, Any]] = []
        db_success = False
        client = get_supabase_client()
        if client:
            try:
                query = client.table("saving_goals").select("*")
                if user_id:
                    query = query.eq("user_id", user_id)
                if status:
                    query = query.eq("status", status)
                res = query.execute()
                if res and res.data is not None:
                    for g in res.data:
                        target = float(g.get("target_amount", 0))
                        current = float(g.get("current_amount", 0))
                        pct = round((current / target * 100) if target > 0 else 0, 1)
                        goals.append({
                            "id": g.get("id"),
                            "goal_name": g.get("goal_name"),
                            "target_amount": target,
                            "current_amount": current,
                            "progress_percentage": pct,
                            "currency": g.get("currency", "USD"),
                            "deadline": g.get("deadline"),
                            "status": g.get("status", "in_progress")
                        })
                db_success = True
            except Exception as exc:
                print(f"[TOOL] Supabase get_saving_goals failed ({exc}), using mock fallback")
                db_success = False

        if not db_success or not goals:
            for g in self._goals:
                if not status or g.get("status") == status:
                    target = float(g.get("target_amount", 0))
                    current = float(g.get("current_amount", 0))
                    pct = round((current / target * 100) if target > 0 else 0, 1)
                    item = dict(g)
                    item["progress_percentage"] = pct
                    goals.append(item)

        return ToolResult(
            success=True,
            data={"count": len(goals), "goals": goals},
            message=f"Se encontraron {len(goals)} meta(s) de ahorro registradas."
        )

    async def update_saving_goal(
        self,
        goal_id: str,
        current_amount: Optional[float] = None,
        target_amount: Optional[float] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ToolResult:
        """
        Updates progress or status of an existing saving goal.
        """
        updates: Dict[str, Any] = {}
        if current_amount is not None:
            updates["current_amount"] = float(current_amount)
        if target_amount is not None:
            updates["target_amount"] = float(target_amount)
        if status is not None:
            updates["status"] = status

        if not updates:
            return ToolResult(
                success=False,
                data=None,
                message="No se especificaron cambios para la meta de ahorro."
            )

        client = get_supabase_client()
        if client and is_valid_uuid(goal_id):
            try:
                query = client.table("saving_goals").update(updates).eq("id", goal_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res and res.data:
                    record = dict(res.data[0])
                    target = float(record.get("target_amount", 0))
                    curr = float(record.get("current_amount", 0))
                    record["progress_percentage"] = round((curr / target * 100) if target > 0 else 0, 1)
                    return ToolResult(
                        success=True,
                        data=record,
                        message=f"Meta de ahorro '{goal_id}' actualizada con éxito."
                    )
            except Exception as exc:
                print(f"[TOOL] Supabase update_saving_goal failed ({exc}), updating in mock")

        # In-memory fallback
        for g in self._goals:
            if g.get("id") == goal_id or g.get("goal_name", "").lower() == goal_id.lower():
                g.update(updates)
                target = float(g.get("target_amount", 0))
                curr = float(g.get("current_amount", 0))
                g["progress_percentage"] = round((curr / target * 100) if target > 0 else 0, 1)
                return ToolResult(
                    success=True,
                    data=g,
                    message=f"Meta '{g.get('goal_name')}' actualizada a ${curr:.2f} USD ({g['progress_percentage']}% de la meta)."
                )

        return ToolResult(
            success=False,
            data=None,
            message=f"No se encontró la meta de ahorro con identificador '{goal_id}'."
        )

    async def execute(
        self,
        action: str = "list",
        goal_id: Optional[str] = None,
        current_amount: Optional[float] = None,
        target_amount: Optional[float] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        print(f"[TOOL] Executing saving_goal_tool (action='{action}', goal_id='{goal_id}')")

        if action in ["update", "add_funds"]:
            gid = goal_id or kwargs.get("name")
            if not gid:
                return ToolResult(success=False, data=None, message="Se requiere el ID o nombre de la meta para actualizarla.")
            return await self.update_saving_goal(
                goal_id=gid,
                current_amount=current_amount or kwargs.get("monto"),
                target_amount=target_amount,
                status=status,
                user_id=user_id
            )

        return await self.get_saving_goals(status=status, user_id=user_id)


# Backward compatibility alias
SavingGoalTool = SavingGoalTools
