"""
Servicio de dashboard y métricas
Maneja la obtención de métricas consolidadas y estadísticas del sistema
"""

import pandas as pd
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from Controllers.dataBaseVectorController import dataBaseVectorController


class DashboardService:
    """Servicio especializado en métricas y dashboard"""
    
    def __init__(self):
        self.db_controller = dataBaseVectorController()
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas consolidadas del dashboard"""
        try:
            dashboard_data = self.db_controller.obtener_metricas_dashboard()
            
            if not dashboard_data["success"]:
                return {"success": False, "message": f"Error: {dashboard_data['message']}"}
            
            response_data = {
                "success": True,
                "timestamp": pd.Timestamp.now().isoformat(),
                "data": {
                    "summary": {
                        "total_vectors": dashboard_data["total_vectors"],
                        "projects_analyzed": dashboard_data["sample_analyzed"],
                        "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "metrics": dashboard_data["metrics"]
                }
            }
            
            return response_data
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
