import {
  HomeIcon,
  BuildingOfficeIcon,
  AcademicCapIcon,
  CpuChipIcon,
  GlobeAltIcon,
  BanknotesIcon,
  ServerIcon,
  InformationCircleIcon
} from "@heroicons/react/24/outline";
import { ROUTES } from "../constants/routes";

export const NAV_ITEMS = [
  {
    label: "Dashboard",
    path: ROUTES.DASHBOARD,
    icon: HomeIcon,
  },
  {
    label: "Companies",
    path: ROUTES.COMPANIES,
    icon: BuildingOfficeIcon,
  },
  {
    label: "Skills",
    path: ROUTES.SKILLS,
    icon: AcademicCapIcon,
  },
  {
    label: "Technology",
    path: ROUTES.TECHNOLOGY,
    icon: CpuChipIcon,
  },
  {
    label: "Geography",
    path: ROUTES.GEOGRAPHY,
    icon: GlobeAltIcon,
  },
  {
    label: "Salary",
    path: ROUTES.SALARY,
    icon: BanknotesIcon,
  },
  {
    label: "System Status",
    path: ROUTES.STATUS,
    icon: ServerIcon,
  },
  {
    label: "About",
    path: ROUTES.ABOUT,
    icon: InformationCircleIcon,
  },
] as const;
