import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../HomeView.vue";
import PredictReport from "../PredictReport.vue";
import FaultAnalysisReport from "../FaultAnalysisReport.vue";

const routes = [
    {
        path: "/",
        name: "home",
        component: HomeView,
    },
    {
        path: "/predict-report",
        name: "predict-report",
        component: PredictReport,
    },
    {
        path: "/fault-analysis",
        name: "fault-analysis",
        component: FaultAnalysisReport,
    },
    {
        path: "/:pathMatch(.*)*",
        redirect: "/",
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;