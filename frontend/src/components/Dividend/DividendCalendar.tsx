import React, { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';

const DividendCalendar: React.FC = () => {
    const [upcomingDividends, setUpcomingDividends] = useState<any[]>([]);
    const [currentMonth, setCurrentMonth] = useState(new Date());

    useEffect(() => {
        fetchUpcomingDividends();
    }, []);

    const fetchUpcomingDividends = async () => {
        try {
            const response = await fetch('http://localhost:8001/api/dividend/calendar');
            if (!response.ok) throw new Error('Failed to fetch calendar');

            const data = await response.json();
            setUpcomingDividends(data.events || []);
        } catch (error) {
            console.error('Calendar fetch error:', error);
        }
    };

    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const firstDayOfMonth = new Date(year, month, 1).getDay();

        const days = [];
        // Add empty slots for days before the month starts
        for (let i = 0; i < firstDayOfMonth; i++) {
            days.push(null);
        }
        // Add days of the month
        for (let i = 1; i <= daysInMonth; i++) {
            days.push(i);
        }
        return days;
    };

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];

    const days = getDaysInMonth(currentMonth);

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Calendar size={20} className="text-blue-600" />
                    배당락일 달력
                </h3>
                <div className="text-sm text-gray-600">
                    {upcomingDividends.length}개의 배당락일
                </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-4">
                    <button
                        onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                        className="px-3 py-1 text-gray-600 hover:bg-gray-100 rounded"
                    >
                        ‹
                    </button>
                    <h4 className="text-lg font-bold text-gray-900">
                        {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                    </h4>
                    <button
                        onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                        className="px-3 py-1 text-gray-600 hover:bg-gray-100 rounded"
                    >
                        ›
                    </button>
                </div>

                <div className="grid grid-cols-7 gap-2">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="text-center text-sm font-semibold text-gray-600 py-2">
                            {day}
                        </div>
                    ))}
                    {days.map((day, index) => (
                        <div
                            key={index}
                            className={`text-center p-2 text-sm ${day ? 'hover:bg-blue-50 cursor-pointer rounded' : ''
                                }`}
                        >
                            {day && (
                                <div className="text-gray-900">{day}</div>
                            )}
                        </div>
                    ))}
                </div>

                {upcomingDividends.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                        <h5 className="text-sm font-semibold text-gray-700 mb-2">다가오는 배당:</h5>
                        <div className="space-y-1">
                            {upcomingDividends.slice(0, 5).map((event, idx) => (
                                <div key={idx} className="text-sm text-gray-600 flex justify-between">
                                    <span className="font-medium text-blue-600">{event.ticker}</span>
                                    <span>${event.amount} - {event.ex_dividend_date}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DividendCalendar;
