import { Setting, SettingType } from "@/interfaces/settings";
import useSettingsStore from "@/stores/settings";

const settings = useSettingsStore;

const use_sidebar: Setting = {
  title: "Use right sidebar",
  type: SettingType.binary,
  source: () => settings().use_sidebar,
  action: () => settings().toggleDisableSidebar(),
};

export default [use_sidebar];