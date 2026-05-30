import * as React from "react";

function ChevronLeft({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  );
}

const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

interface CalendarProps {
  date: Date;
  onDateChange: (date: Date) => void;
}

export function Calendar({ date, onDateChange }: CalendarProps) {
  const today = new Date();
  const currentMonth = date.getMonth();
  const currentYear = date.getFullYear();
  
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
  const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0);
  const daysInMonth = lastDayOfMonth.getDate();
  const startingDayOfWeek = firstDayOfMonth.getDay();
  
  const previousMonth = new Date(currentYear, currentMonth - 1, 1);
  const nextMonth = new Date(currentYear, currentMonth + 1, 1);
  
  const days = [];
  
  // Add empty cells for days before the first day of the month
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push(null);
  }
  
  // Add cells for each day of the month
  for (let day = 1; day <= daysInMonth; day++) {
    days.push(new Date(currentYear, currentMonth, day));
  }
  
  return (
    <div className="border rounded-lg">
      <div className="flex items-center justify-between p-4 border-b">
        <button
          onClick={() => onDateChange(previousMonth)}
          className="p-1 rounded-full hover:bg-gray-100"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h2 className="text-lg font-medium">
          {months[currentMonth]} {currentYear}
        </h2>
        <button
          onClick={() => onDateChange(nextMonth)}
          className="p-1 rounded-full hover:bg-gray-100"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
      
      <div className="grid grid-cols-7 gap-1 p-2">
        {weekdays.map((day) => (
          <div key={day} className="text-center text-sm font-medium text-muted-foreground">
            {day}
          </div>
        ))}
        
        {days.map((day, index) => (
          <button
            key={index}
            onClick={() => day && onDateChange(day)}
            className={`h-10 w-10 rounded-md text-sm transition-colors ${
              day
                ? day.toDateString() === today.toDateString()
                  ? "bg-primary text-primary-foreground"
                  : day.toDateString() === date.toDateString()
                  ? "bg-secondary text-secondary-foreground"
                  : "hover:bg-gray-100"
                : "invisible"
            }`}
          >
            {day ? day.getDate() : null}
          </button>
        ))}
      </div>
    </div>
  );
}