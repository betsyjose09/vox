import React, { useEffect, useState } from 'react';
import { getPublicInfo } from '../lib/api';
import { MapPin, Phone, Mail } from 'lucide-react';

const WAVE_HEIGHTS = [18, 34, 52, 78, 95, 70, 45, 60, 88, 100, 64, 38, 55, 82, 96, 58, 30, 48, 74, 92, 66, 40, 26, 14];

const WaveStrip: React.FC<{ play?: boolean }> = ({ play }) => (
  <div className={`wave-strip ${play ? 'play' : ''}`} aria-hidden="true">
    {WAVE_HEIGHTS.map((h, i) => (
      <i key={i} style={{ ['--h' as any]: h, ['--i' as any]: i }} />
    ))}
  </div>
);

export const Home: React.FC<{ onNavigateToAssistant: () => void }> = ({ onNavigateToAssistant }) => {
  const [info, setInfo] = useState<any>(null);

  useEffect(() => {
    getPublicInfo().then((data) => setInfo(data)).catch(console.error);
  }, []);

  return (
    <div className="home-container">
      <div className="hero-card">
        <h2 className="hero-title">The college office, on voice.</h2>
        <p className="hero-lede">
          KIT VOX answers questions about admissions, fees, attendance, timetables and leave
          from official college records — and speaks each reply aloud. Sensitive requests ask
          for confirmation before anything is submitted.
        </p>
        <WaveStrip play />
        <button className="btn-primary" onClick={onNavigateToAssistant}>
          Open the assistant
        </button>
      </div>

      {info && (
        <>
          <section>
            <h3 className="section-title">Academic programmes 2026–27</h3>
            <p className="section-note">Fees and seats as published by the college system.</p>
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>Programme</th>
                  <th>Duration</th>
                  <th>Annual fee</th>
                  <th>Eligibility</th>
                </tr>
              </thead>
              <tbody>
                {info.courses?.map((c: any, i: number) => (
                  <tr key={i}>
                    <td className="cell-strong">{c.title}</td>
                    <td>{c.duration}</td>
                    <td className="cell-num">{c.annual_fee}</td>
                    <td>{c.eligibility}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h3 className="section-title">Upcoming placement drives</h3>
            <p className="section-note">
              {info.today?.date
                ? `Campus date: ${info.today.date}${info.today.weekday_name ? ` (${info.today.weekday_name})` : ''}.`
                : ''}{' '}
              Apply through the placement cell before the deadline.
            </p>
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Track</th>
                  <th>Min CGPA</th>
                  <th>Departments</th>
                  <th>Deadline</th>
                  <th>Seats left</th>
                </tr>
              </thead>
              <tbody>
                {info.placements?.map((d: any, i: number) => (
                  <tr key={i}>
                    <td className="cell-strong">{d.company}</td>
                    <td>{d.category === 'dream' ? 'Dream offer' : 'Regular'}</td>
                    <td className="cell-num">{d.min_cgpa}</td>
                    <td>{(d.departments || []).join(', ')}</td>
                    <td className="cell-num">{d.deadline}</td>
                    <td className="cell-num">
                      <span className={d.seats_left !== undefined && d.seats_left <= 2 ? 'seats-low' : ''}>
                        {d.seats_left}/{d.seats_total}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="contact-block">
            <h4 className="contact-title">Campus contact</h4>
            <div className="contact-row">
              <MapPin size={15} color="#237589" />
              <span>{info.college.location}</span>
            </div>
            <div className="contact-row">
              <Phone size={15} color="#237589" />
              <span>{info.college.helpline}</span>
            </div>
            <div className="contact-row">
              <Mail size={15} color="#237589" />
              <span>{info.college.email}</span>
            </div>
          </section>
        </>
      )}
    </div>
  );
};
