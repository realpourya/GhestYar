from pathlib import Path
import sys

project = Path(sys.argv[1])
main = project / "app/src/main/java/com/pourya/ghestyar/MainActivity.java"
gradle = project / "app/build.gradle"
source = main.read_text(encoding="utf-8")

source = source.replace("    int calendarMonthOffset = 0;\n",
                        "    int calendarMonthOffset = 0;\n    int calendarSelectedDay = -1;\n", 1)
source = source.replace("TextView badge = t(persianNumber(count), 14, Color.WHITE);",
                        "TextView badge = t(persianNumber(count), 11, Color.WHITE);", 1)
source = source.replace("titleRow.addView(badge, new LinearLayout.LayoutParams(dp(27), dp(27)));",
                        "titleRow.addView(badge, new LinearLayout.LayoutParams(dp(21), dp(21)));", 1)

start = source.index("    void renderCalendar() {")
end = source.index("    ArrayList<Installment> installmentsForDay(int day) {", start)
calendar_method = r'''    void renderCalendar() {
        int[] ym = displayedPersianMonth();
        int year = ym[0], month = ym[1];
        final int calendarBg = Color.rgb(17, 19, 20);
        final int cellBg = Color.rgb(47, 49, 50);
        final int fridayBg = Color.rgb(91, 48, 13);
        final int selectedBg = Color.rgb(54, 126, 128);
        final int normalDay = Color.rgb(218, 231, 211);
        final int fridayText = Color.rgb(255, 177, 105);
        final int muted = Color.rgb(164, 174, 164);

        LinearLayout calendar = new LinearLayout(this);
        calendar.setOrientation(LinearLayout.VERTICAL);
        calendar.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        calendar.setPadding(dp(7), dp(8), dp(7), dp(10));
        calendar.setBackground(round(calendarBg, dp(18)));

        LinearLayout monthBar = new LinearLayout(this);
        monthBar.setGravity(Gravity.CENTER_VERTICAL);
        monthBar.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        monthBar.setPadding(dp(8), 0, dp(8), 0);
        monthBar.setBackground(round(Color.rgb(0, 112, 108), dp(16)));

        TextView prev = t("ماه قبل  ‹", 12, Color.rgb(196, 225, 220));
        prev.setGravity(Gravity.CENTER);
        prev.setSingleLine(true);
        TextView title = t("تقویم " + persianMonthName(month) + " " + persianNumber(year), 19, Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        title.setSingleLine(true);
        TextView next = t("›  ماه بعد", 12, Color.rgb(196, 225, 220));
        next.setGravity(Gravity.CENTER);
        next.setSingleLine(true);
        monthBar.addView(prev, new LinearLayout.LayoutParams(dp(78), dp(54)));
        monthBar.addView(title, new LinearLayout.LayoutParams(0, dp(54), 1));
        monthBar.addView(next, new LinearLayout.LayoutParams(dp(78), dp(54)));
        calendar.addView(monthBar, new LinearLayout.LayoutParams(-1, dp(54)));
        prev.setOnClickListener(v -> { calendarMonthOffset--; renderInstallments(); });
        next.setOnClickListener(v -> { calendarMonthOffset++; renderInstallments(); });

        LinearLayout weekdays = new LinearLayout(this);
        weekdays.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        weekdays.setPadding(0, dp(10), 0, dp(5));
        String[] week = {"شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"};
        for (int i = 0; i < week.length; i++) {
            TextView w = t(week[i], 9, i == 6 ? fridayText : Color.rgb(112, 190, 190));
            w.setGravity(Gravity.CENTER);
            w.setSingleLine(true);
            weekdays.addView(w, new LinearLayout.LayoutParams(0, dp(31), 1));
        }
        calendar.addView(weekdays, new LinearLayout.LayoutParams(-1, dp(36)));

        Calendar first = PersianDate.toGregorian(year, month, 1);
        int offset = first.get(Calendar.DAY_OF_WEEK) % 7;
        int count = daysInPersianMonth(year, month);
        int rows = (offset + count + 6) / 7;
        int[] now = PersianDate.now();
        int todayDay = (now[0] == year && now[1] == month) ? now[2] : -1;
        if (calendarSelectedDay < 1 || calendarSelectedDay > count) calendarSelectedDay = todayDay;

        for (int row = 0; row < rows; row++) {
            LinearLayout weekRow = new LinearLayout(this);
            weekRow.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
            weekRow.setGravity(Gravity.CENTER_VERTICAL);
            for (int col = 0; col < 7; col++) {
                int day = row * 7 + col - offset + 1;
                FrameLayout cell = new FrameLayout(this);
                LinearLayout.LayoutParams cellLp = new LinearLayout.LayoutParams(0, dp(66), 1);
                cellLp.setMargins(dp(2), dp(2), dp(2), dp(2));
                if (day >= 1 && day <= count) {
                    ArrayList<Installment> due = installmentsForDay(day);
                    boolean anyUnpaid = false;
                    for (Installment x : due) {
                        if (!sp.getBoolean(paidKey(x, year, month), false)) anyUnpaid = true;
                    }
                    boolean friday = col == 6;
                    boolean selected = day == calendarSelectedDay;
                    int background = selected ? selectedBg : (friday ? fridayBg : cellBg);
                    cell.setBackground(round(background, dp(11)));
                    cell.setElevation(dp(selected ? 2 : 0));

                    int numberColor = selected ? Color.WHITE : (!due.isEmpty()
                            ? (anyUnpaid ? Color.rgb(224, 78, 88) : Color.rgb(75, 190, 125))
                            : (friday ? fridayText : normalDay));
                    TextView number = t(persianNumber(day), 22, numberColor);
                    number.setGravity(Gravity.CENTER);
                    number.setTypeface(null, android.graphics.Typeface.BOLD);
                    cell.addView(number, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));

                    if (!due.isEmpty()) {
                        View dot = new View(this);
                        int dotColor = anyUnpaid ? Color.rgb(205, 55, 70) : Color.rgb(45, 157, 94);
                        dot.setBackground(round(dotColor, dp(4)));
                        FrameLayout.LayoutParams dlp = new FrameLayout.LayoutParams(dp(6), dp(6), Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
                        dlp.bottomMargin = dp(4);
                        cell.addView(dot, dlp);
                    }
                    cell.setOnClickListener(v -> {
                        calendarSelectedDay = day;
                        renderInstallments();
                        showCalendarDayDetails(year, month, day);
                    });
                    cell.setOnLongClickListener(v -> {
                        if (due.isEmpty()) {
                            Toast.makeText(MainActivity.this, "برای این روز قسطی ثبت نشده است", Toast.LENGTH_SHORT).show();
                            return true;
                        }
                        calendarSelectedDay = day;
                        renderInstallments();
                        showCalendarDayEditOptions(year, month, day);
                        return true;
                    });
                }
                weekRow.addView(cell, cellLp);
            }
            calendar.addView(weekRow, new LinearLayout.LayoutParams(-1, dp(70)));
        }

        LinearLayout legend = new LinearLayout(this);
        legend.setGravity(Gravity.CENTER);
        legend.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        TextView unpaidLegend = t("● پرداخت‌نشده", 10, muted);
        TextView paidLegend = t("● پرداخت‌شده", 10, muted);
        unpaidLegend.setGravity(Gravity.CENTER);
        paidLegend.setGravity(Gravity.CENTER);
        legend.addView(unpaidLegend, new LinearLayout.LayoutParams(-2, dp(32)));
        legend.addView(paidLegend, new LinearLayout.LayoutParams(-2, dp(32)));
        calendar.addView(legend);

        LinearLayout.LayoutParams calendarLp = new LinearLayout.LayoutParams(-1, -2);
        calendarLp.setMargins(0, dp(5), 0, dp(8));
        list.addView(calendar, calendarLp);
    }

'''
source = source[:start] + calendar_method + source[end:]

start = source.index("    void showCalendarDayDetails(int year, int month, int day) {")
end = source.index("    void showCreatorInfo() {", start)
details = r'''    void showCalendarDayDetails(int year, int month, int day) {
        ArrayList<Installment> due = installmentsForDay(day);
        if (due.isEmpty()) {
            new AlertDialog.Builder(this).setTitle("روز " + persianNumber(day) + " " + persianMonthName(month))
                    .setMessage("برای این روز قسطی ثبت نشده است.").setPositiveButton("باشه", null).show();
            return;
        }
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(16), dp(8), dp(16), dp(8));
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("اقساط " + persianNumber(day) + " " + persianMonthName(month))
                .setView(panel).setPositiveButton("بستن", null).create();
        for (Installment x : due) {
            boolean isPaid = sp.getBoolean(paidKey(x, year, month), false);
            LinearLayout row = new LinearLayout(this);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(0, dp(7), 0, dp(7));
            row.setOrientation(LinearLayout.HORIZONTAL);
            TextView info = t(x.name + "\n" + fmtAmount(x.amount) + "\n" + (isPaid ? "پرداخت‌شده" : "پرداخت‌نشده"), 13,
                    isPaid ? Color.rgb(35,135,75) : Color.rgb(190,45,55));
            info.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
            row.addView(info, new LinearLayout.LayoutParams(0, -2, 1));
            Button toggle = new Button(this);
            toggle.setText(isPaid ? "برگشت به پرداخت‌نشده" : "ثبت پرداخت");
            toggle.setTextSize(10);
            toggle.setOnClickListener(v -> {
                boolean newValue = !sp.getBoolean(paidKey(x, year, month), false);
                sp.edit().putBoolean(paidKey(x, year, month), newValue).apply();
                dialog.dismiss();
                renderInstallments();
                showCalendarDayDetails(year, month, day);
            });
            row.addView(toggle, new LinearLayout.LayoutParams(-2, dp(42)));
            panel.addView(row);
            View divider = new View(this);
            divider.setBackgroundColor(isSystemDarkMode() ? Color.DKGRAY : Color.LTGRAY);
            panel.addView(divider, new LinearLayout.LayoutParams(-1, dp(1)));
        }
        dialog.show();
    }

    void showCalendarDayEditOptions(int year, int month, int day) {
        ArrayList<Installment> due = installmentsForDay(day);
        if (due.isEmpty()) return;
        if (due.size() == 1) {
            int index = items.indexOf(due.get(0));
            if (index >= 0) showEditor(index);
            return;
        }
        String[] names = new String[due.size()];
        for (int i = 0; i < due.size(); i++) names[i] = due.get(i).name;
        new AlertDialog.Builder(this)
                .setTitle("کدام قسط ویرایش شود؟")
                .setItems(names, (dialog, which) -> {
                    int index = items.indexOf(due.get(which));
                    if (index >= 0) showEditor(index);
                })
                .setNegativeButton("انصراف", null)
                .show();
    }

'''
source = source[:start] + details + source[end:]

# Ensure malformed source newline sequences cannot survive the patch.
source = source.replace('"' + chr(10) + '"', '"\\n"')
main.write_text(source, encoding="utf-8")

build = gradle.read_text(encoding="utf-8")
build = build.replace("versionCode 20; versionName '3.0'", "versionCode 21; versionName '3.1'")
gradle.write_text(build, encoding="utf-8")

print("Applied GhestYar 3.1 calendar redesign, Persian RTL grid, smaller badges, and long-press edit.")
