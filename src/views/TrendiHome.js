import React, { useState } from 'react';
import './TrendiHome.css'; // Import the CSS styles

const Home = () => {
  const [steps] = useState([
    {
      title: 'Step 1',
      description: "Click on 'Trending' tab and choose a trend",
      image:
        'https://trendiai.s3.amazonaws.com/main/main_step1.png?AWSAccessKeyId=AKIAVRUVUT7MXIJPOIGH&Signature=o8BSIhRELkySn4uB5mNmLobrl4w%3D&Expires=1750755483',
    },
    {
      title: 'Step 2',
      description: "Look at each trend's breakdown",
      image:
        'https://trendiai.s3.amazonaws.com/main/main_step2.png?AWSAccessKeyId=AKIAVRUVUT7MXIJPOIGH&Signature=%2FPOCheXRmJMiDoMzzLta%2BJbaE%2FI%3D&Expires=1750755483',
    },
    {
      title: 'Step 3',
      description: "Click 'Recreate' to generate the template",
      image:
        'https://trendiai.s3.amazonaws.com/main/main_step3.png?AWSAccessKeyId=AKIAVRUVUT7MXIJPOIGH&Signature=bv%2FhjNTj5gQl0wR4EJ8jNm715A4%3D&Expires=1750755483',
    },
    {
      title: 'Step 4',
      description: 'Upload files to template spaces',
      image:
        'https://trendiai.s3.amazonaws.com/main/main_step4.png?AWSAccessKeyId=AKIAVRUVUT7MXIJPOIGH&Signature=hArPXtlZW39RGL3NVSOxDT8uwW4%3D&Expires=1750755483',
    },
    {
      title: 'Step 5',
      description: 'Download synced video for social media!',
      image:
        'https://trendiai.s3.amazonaws.com/main/main_step5.png?AWSAccessKeyId=AKIAVRUVUT7MXIJPOIGH&Signature=%2BgqZbmp1K3Fs%2FSuiO73Sc0UtRqc%3D&Expires=1750755483',
    },
  ]);

  return (
    <div className="home">
      <div className="title">
        <img src="../assets/whiteLogo.png" alt="Trendi" className="logo" />
        <h1 className="title">Trendi.ai</h1>
        <p className="catchphrase">Templates to recreate the latest trends!</p>
      </div>
      
      <div className="diagonal"></div>

      <div className="roadmap">
        {steps.map((step, index) => (
          <div key={index} className={`step step-${index % 2 === 0 ? 'left' : 'right'}`}>
            <div className="step-content">
              <div className="step-words">
                <h2>{step.title}</h2>
                <p>{step.description}</p>
              </div>
              <img src={step.image} alt={step.title} />
            </div>
          </div>
        ))}
      </div>

      <div className="diagonal" style={{ background: 'linear-gradient(5deg, #0d194e 50%, white 50%)' }}></div>

      <div className="title">
        <h2 style={{ marginBottom: '20px' }}>Future Functionalities</h2>
        <p>We're excited to share some upcoming features that will enhance your experience with Trendi.ai:</p>
        <ul className="future-features">
          <li>Continuous addition of new templates to keep up with the latest trends</li>
          <li>Personalized trend recommendations based on your company's products</li>
          <li>AI-driven ideas to replicate trends effectively tailored to your business needs</li>
        </ul>
      </div>

      <div className="diagonal"></div>

      <div className="title" style={{ background: 'white', color: '#0d194e' }}>
        <h2 style={{ marginBottom: '20px' }}>Upcoming Fixes</h2>
        <p>Features that are currently being developed:</p>
        <ul className="future-features" style={{ color: '#0d194e' }}>
          <li>Accounts will allow users to 'Favorite' trends while browsing</li>
          <li>Improved UI to select video segments</li>
          <li>Customizable templates made by users uploading their own videos</li>
        </ul>
      </div>

      <div className="diagonal" style={{ background: 'linear-gradient(5deg, #0d194e 50%, white 50%)' }}></div>
    </div>
  );
};

export default Home;