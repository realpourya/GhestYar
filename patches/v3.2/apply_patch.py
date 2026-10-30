from pathlib import Path
import sys

project = Path(sys.argv[1])
main = project / "app/src/main/java/com/pourya/ghestyar/MainActivity.java"
gradle = project / "app/build.gradle"
source = main.read_text(encoding="utf-8")

old_palette = """        final int calendarBg = Color.rgb(17, 19, 20);
        final int cellBg = Color.rgb(47, 49, 50);
        final int fridayBg = Color.rgb(91, 48, 13);
        final int selectedBg = Color.rgb(54, 126, 128);
        final int normalDay = Color.rgb(218, 231, 211);
        final int fridayText = Color.rgb(255, 177, 105);
        final int muted = Color.rgb(164, 174, 164);
"""
new_palette = """        final boolean darkMode = isSystemDarkMode();
        final int calendarBg = darkMode ? Color.rgb(17, 19, 20) : BG;
        final int cellBg = darkMode ? Color.rgb(47, 49, 50) : Color.rgb(229, 234, 241);
        final int fridayBg = darkMode ? Color.rgb(91, 48, 13) : Color.rgb(252, 229, 208);
        final int selectedBg = Color.rgb(54, 126, 128);
        final int normalDay = darkMode ? Color.rgb(218, 231, 211) : TEXT;
        final int fridayText = darkMode ? Color.rgb(255, 177, 105) : Color.rgb(174, 91, 35);
        final int muted = darkMode ? Color.rgb(164, 174, 164) : SECONDARY;
"""
if old_palette not in source:
    raise SystemExit("Could not locate v3.1 calendar color palette; refusing to patch an unexpected source.")
source = source.replace(old_palette, new_palette, 1)

old_weekday = 'TextView w = t(week[i], 9, i == 6 ? fridayText : Color.rgb(112, 190, 190));'
new_weekday = 'TextView w = t(week[i], 9, i == 6 ? fridayText : (darkMode ? Color.rgb(112, 190, 190) : BLUE));'
if old_weekday not in source:
    raise SystemExit("Could not locate calendar weekday styling.")
source = source.replace(old_weekday, new_weekday, 1)

old_legend = """        LinearLayout legend = new LinearLayout(this);
        legend.setGravity(Gravity.CENTER);
        legend.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        TextView unpaidLegend = t("● پرداخت‌نشده", 10, muted);
        TextView paidLegend = t("● پرداخت‌شده", 10, muted);
        unpaidLegend.setGravity(Gravity.CENTER);
        paidLegend.setGravity(Gravity.CENTER);
        legend.addView(unpaidLegend, new LinearLayout.LayoutParams(-2, dp(32)));
        legend.addView(paidLegend, new LinearLayout.LayoutParams(-2, dp(32)));
        calendar.addView(legend);

"""
if old_legend not in source:
    raise SystemExit("Could not locate the paid/unpaid legend; refusing to remove an unexpected section.")
source = source.replace(old_legend, "", 1)

# Rebuild the calendar immediately when Android reports a system theme change.
old_config = """            if (Build.VERSION.SDK_INT >= 26) {
                getWindow().getDecorView().setSystemUiVisibility(isSystemDarkMode() ? 0 : View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
            }
"""
new_config = """            if (Build.VERSION.SDK_INT >= 26) {
                getWindow().getDecorView().setSystemUiVisibility(isSystemDarkMode() ? 0 : View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
            }
            if (showingInstallments && calendarDisplay && list != null) {
                renderInstallments();
            }
"""
if old_config not in source:
    raise SystemExit("Could not locate onConfigurationChanged block.")
source = source.replace(old_config, new_config, 1)

main.write_text(source, encoding="utf-8")
build = gradle.read_text(encoding="utf-8")
build = build.replace("versionCode 21; versionName '3.1'", "versionCode 22; versionName '3.2'")
if "versionCode 22; versionName '3.2'" not in build:
    raise SystemExit("Could not update app version to 3.2.")
gradle.write_text(build, encoding="utf-8")
print("Applied v3.2 system-theme calendar colors, removed legend, and bumped version.")
