// Schedule.js
import React from 'react';
import './Calendar.css'; // Make sure this CSS file matches the updates.

const Schedule = () => {
  // Define time intervals
  const timeIntervals = [
    '8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM', '12:00 AM', '1:00 PM', 
    '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM', '6:00 PM',
    '7:00 PM', '8:00 PM',
  ];

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (

    <div className="weekly-schedule">
        <div className="date-row">
                {daysOfWeek.map((day, index) => (
                <div className="day-label" key={index}>{day}</div>
                ))}
        </div>
        {timeIntervals.map((time, index) => (
            <div className="row" key={index}>
            <div className="day-columns">
                {Array.from({ length: 7 }).map((_, idx) => (
                <div className="block-container" key={idx}>
                    {index === 0 && idx === 1 && <div className="block red"></div>}
                    {index === 1 && idx === 1 && <div className="block blue"></div>}
                    {index === 2 && idx === 2 && <div className="block yellow"></div>}
                    {index === 3 && idx === 3 && <div className="block green"></div>}
                    {index === 4 && idx === 4 && <div className="block red"></div>}
                </div>
                ))}
            </div>
            </div>
        ))}
        </div>

    
  );
};

export default Schedule;
