from pathlib import Path
import sys

project = Path(sys.argv[1])
main = project / "app/src/main/java/com/pourya/ghestyar/MainActivity.java"
receiver = project / "app/src/main/java/com/pourya/ghestyar/ReminderReceiver.java"
gradle = project / "app/build.gradle"
s = main.read_text(encoding="utf-8")

start = s.index("    int reminderRequestCode(Installment x, boolean overdue) {")
end = s.index("\n}\n", start)
new_methods = r'''    int reminderRequestCode(Installment x, boolean overdue) {
        int base = 1000 + (x.id.hashCode() & 0x3fffffff);
        return base * 2 + (overdue ? 1 : 0);
    }

    int reminderRequestCode(Installment x, int kind) {
        return (x.id.hashCode() & 0x0fffffff) * 3 + kind;
    }

    void cancelReminder(Installment x) {
        AlarmManager am = (AlarmManager) getSystemService(ALARM_SERVICE);
        Intent old = new Intent(this, ReminderReceiver.class);
        old.putExtra("id", x.id);
        old.putExtra("overdue", true);
        PendingIntent oldPi = PendingIntent.getBroadcast(this, reminderRequestCode(x, true), old,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        am.cancel(oldPi);
        oldPi.cancel();
        for (int kind = 0; kind < 3; kind++) {
            Intent in = new Intent(this, ReminderReceiver.class);
            in.putExtra("id", x.id);
            in.putExtra("kind", kind);
            PendingIntent pi = PendingIntent.getBroadcast(this, reminderRequestCode(x, kind), in,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            am.cancel(pi);
            pi.cancel();
        }
    }

    int jalaliMonthLength(int year, int month) {
        if (month <= 6) return 31;
        if (month <= 11) return 30;
        Calendar thisYear = PersianDate.toGregorian(year, 1, 1);
        Calendar nextYear = PersianDate.toGregorian(year + 1, 1, 1);
        long days = (nextYear.getTimeInMillis() - thisYear.getTimeInMillis()) / 86400000L;
        return days >= 366 ? 30 : 29;
    }

    Calendar installmentDueDate(int year, int month, int day) {
        return PersianDate.toGregorian(year, month, Math.min(day, jalaliMonthLength(year, month)));
    }

    void scheduleAll() {
        AlarmManager am = (AlarmManager) getSystemService(ALARM_SERVICE);
        long now = System.currentTimeMillis();
        for (Installment x : items) {
            cancelReminder(x);
            int[] p = PersianDate.now();
            int year = p[0], month = p[1];
            Calendar due = installmentDueDate(year, month, x.day);
            due.set(Calendar.HOUR_OF_DAY, 12);
            due.set(Calendar.MINUTE, 0);
            due.set(Calendar.SECOND, 0);
            due.set(Calendar.MILLISECOND, 0);
            Calendar overdue = (Calendar) due.clone();
            overdue.add(Calendar.DAY_OF_MONTH, 1);
            if (overdue.getTimeInMillis() <= now) {
                month++;
                if (month == 13) { month = 1; year++; }
                due = installmentDueDate(year, month, x.day);
                due.set(Calendar.HOUR_OF_DAY, 12);
                due.set(Calendar.MINUTE, 0);
                due.set(Calendar.SECOND, 0);
                due.set(Calendar.MILLISECOND, 0);
                overdue = (Calendar) due.clone();
                overdue.add(Calendar.DAY_OF_MONTH, 1);
            }
            Calendar before = (Calendar) due.clone();
            before.add(Calendar.DAY_OF_MONTH, -1);
            scheduleReminder(am, x, before, year, month, x.day, 0);
            scheduleReminder(am, x, due, year, month, x.day, 1);
            scheduleReminder(am, x, overdue, year, month, x.day, 2);
        }
    }

    void scheduleReminder(AlarmManager am, Installment x, Calendar when,
                          int dueYear, int dueMonth, int dueDay, int kind) {
        if (when.getTimeInMillis() <= System.currentTimeMillis()) return;
        Intent in = new Intent(this, ReminderReceiver.class);
        in.putExtra("name", x.name);
        in.putExtra("day", x.day);
        in.putExtra("id", x.id);
        in.putExtra("kind", kind);
        in.putExtra("dueYear", dueYear);
        in.putExtra("dueMonth", dueMonth);
        in.putExtra("dueDay", dueDay);
        PendingIntent pi = PendingIntent.getBroadcast(this, reminderRequestCode(x, kind), in,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        try {
            if (Build.VERSION.SDK_INT >= 31 && am.canScheduleExactAlarms())
                am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when.getTimeInMillis(), pi);
            else
                am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when.getTimeInMillis(), pi);
        } catch (SecurityException e) {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when.getTimeInMillis(), pi);
        }
    }
'''
main.write_text(s[:start] + new_methods + s[end:], encoding="utf-8")

receiver.write_text(r'''package com.pourya.ghestyar;

import android.app.*;
import android.content.*;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.*;
import java.util.Calendar;

public class ReminderReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        String id = i.getStringExtra("id");
        if (id == null) id = "unknown";
        String name = i.getStringExtra("name");
        int dueYear = i.getIntExtra("dueYear", 0);
        int dueMonth = i.getIntExtra("dueMonth", 0);
        int dueDay = i.getIntExtra("dueDay", 1);
        int kind = i.hasExtra("kind") ? i.getIntExtra("kind", 2) : 2;
        if (kind < 0 || kind > 2) kind = 2;

        String paidKey = "paid_" + id + "_" + dueYear + "_" + dueMonth;
        SharedPreferences payments = c.getSharedPreferences("installments", Context.MODE_PRIVATE);
        boolean alreadyPaid = payments.getBoolean(paidKey, false);
        String[] kinds = {"before", "due", "overdue"};
        String occurrence = id + "_" + dueYear + "_" + dueMonth + "_" + dueDay + "_" + kinds[kind];
        SharedPreferences sent = c.getSharedPreferences("reminder_sent", Context.MODE_PRIVATE);
        String sentKey = "sent_" + occurrence;
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        boolean enabled = Build.VERSION.SDK_INT < 24 || nm.areNotificationsEnabled();

        if (!alreadyPaid && enabled && !sent.getBoolean(sentKey, false)) {
            sent.edit().putBoolean(sentKey, true).apply();
            String channel = "ghest_reminders_v2";
            Uri sound = android.provider.Settings.System.DEFAULT_NOTIFICATION_URI;
            AudioAttributes aa = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
            if (Build.VERSION.SDK_INT >= 26) {
                NotificationChannel nc = new NotificationChannel(channel, "یادآوری اقساط", NotificationManager.IMPORTANCE_HIGH);
                nc.setDescription("یادآوری پیش از موعد، روز سررسید و اقساط عقب‌افتاده");
                nc.setSound(sound, aa);
                nc.enableVibration(true);
                nm.createNotificationChannel(nc);
            }
            String title;
            String body;
            if (kind == 0) {
                title = "یادآوری موعد قسط";
                body = "فردا موعد پرداخت قسط «" + (name == null ? "" : name) + "» است.";
            } else if (kind == 1) {
                title = "امروز موعد پرداخت قسط است";
                body = "امروز موعد پرداخت قسط «" + (name == null ? "" : name) + "» است.";
            } else {
                title = "یادآوری قسط";
                body = "قسط عقب افتاده داری ستون ☹️";
            }
            Notification.Builder b = Build.VERSION.SDK_INT >= 26
                    ? new Notification.Builder(c, channel)
                    : new Notification.Builder(c).setSound(sound);
            b.setSmallIcon(com.pourya.ghestyar.R.drawable.ic_launcher)
                    .setContentTitle(title).setContentText(body)
                    .setStyle(new Notification.BigTextStyle().bigText(body))
                    .setAutoCancel(true).setPriority(Notification.PRIORITY_HIGH)
                    .setSound(sound).setDefaults(Notification.DEFAULT_VIBRATE);
            nm.notify((id + "_" + dueYear + "_" + dueMonth + "_" + kind).hashCode(), b.build());
        }

        // Keep each of the three reminder streams recurring monthly.
        if (dueYear > 0 && dueMonth > 0) {
            int nextYear = dueYear;
            int nextMonth = dueMonth + 1;
            if (nextMonth == 13) { nextMonth = 1; nextYear++; }
            int length;
            if (nextMonth <= 6) length = 31;
            else if (nextMonth <= 11) length = 30;
            else {
                Calendar a = PersianDate.toGregorian(nextYear, 1, 1);
                Calendar b = PersianDate.toGregorian(nextYear + 1, 1, 1);
                length = (b.getTimeInMillis() - a.getTimeInMillis()) / 86400000L >= 366 ? 30 : 29;
            }
            Calendar next = PersianDate.toGregorian(nextYear, nextMonth, Math.min(dueDay, length));
            if (kind == 0) next.add(Calendar.DAY_OF_MONTH, -1);
            else if (kind == 2) next.add(Calendar.DAY_OF_MONTH, 1);
            next.set(Calendar.HOUR_OF_DAY, 12);
            next.set(Calendar.MINUTE, 0);
            next.set(Calendar.SECOND, 0);
            next.set(Calendar.MILLISECOND, 0);
            Intent nextIntent = new Intent(c, ReminderReceiver.class);
            nextIntent.putExtra("id", id);
            nextIntent.putExtra("name", name);
            nextIntent.putExtra("day", dueDay);
            nextIntent.putExtra("kind", kind);
            nextIntent.putExtra("dueYear", nextYear);
            nextIntent.putExtra("dueMonth", nextMonth);
            nextIntent.putExtra("dueDay", dueDay);
            int request = (id.hashCode() & 0x0fffffff) * 3 + kind;
            PendingIntent pi = PendingIntent.getBroadcast(c, request, nextIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
            try {
                if (Build.VERSION.SDK_INT >= 31 && am.canScheduleExactAlarms())
                    am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.getTimeInMillis(), pi);
                else
                    am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.getTimeInMillis(), pi);
            } catch (SecurityException e) {
                am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.getTimeInMillis(), pi);
            }
        }
    }
}
''', encoding="utf-8")

g = gradle.read_text(encoding="utf-8")
if "versionCode 22; versionName '3.2'" not in g:
    raise SystemExit("Expected v3.2 version marker not found")
gradle.write_text(g.replace("versionCode 22; versionName '3.2'", "versionCode 23; versionName '3.3'", 1), encoding="utf-8")
print("Applied v3.3 three-stage monthly reminders.")
