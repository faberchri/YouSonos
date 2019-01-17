import React from "react";
import {currentTrack, NULL_TRACK, Track} from "./api";

import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import Card from '@material-ui/core/Card';
import CardMedia from '@material-ui/core/CardMedia';
import Typography from '@material-ui/core/Typography';
import PlayPauseControl from "./PlayPauseControl";
import Grid from '@material-ui/core/Grid';
import TrackProgressControl from "./TrackProgressControl";

var Textfit = require('react-textfit').default;


interface State {
    currentTrack: Track;
}

const styles = (theme: Theme) => createStyles({
    card: {
        display: 'flex',
        margin: '5px',
        height: '300px'
    },
    cover: {
        backgroundColor: 'black',
        width: '150px',
        minWidth: '150px',
        maxWidth: '150px'
    },
    gridContainer: {
        padding: '5px',
        width: 'calc(100% - 150px)',
    },
    titleText: {
        height: '25px',
        lineHeight: '1'
    },
    artistText: {
        height: '16px',
        lineHeight: '1'
    }
});

interface Props extends WithStyles<typeof styles> {}

class CurrentTrackPanel extends React.Component<Props, State> {


    constructor(props: Props) {
        super(props);
        this.state = CurrentTrackPanel.getNullTrack();
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
    }

    componentDidMount() {
        currentTrack(this.setCurrentTrack)
    }

    setCurrentTrack(track: Track): void {
        if (track.track_type === 'null') {
            this.setState(CurrentTrackPanel.getNullTrack());
        } else {
            this.setState({currentTrack: track});
        }
    }

    static getNullTrack(): State {
        return {currentTrack: NULL_TRACK};
    }


    render() {

        const { classes } = this.props;


        return (

            <Card className={classes.card}>
                <CardMedia
                    className={classes.cover}
                    image={this.state.currentTrack.cover_url}
                    title={this.state.currentTrack.title}
                />
                <Grid container className={classes.gridContainer}>
                    <Grid item xs={12} >
                        <Typography component="h6" variant="h6" align={"left"} className={classes.titleText}>
                            <Textfit mode="single" max={25} >
                            {this.state.currentTrack.title}
                            </Textfit>
                        </Typography>
                    </Grid>
                    <Grid item xs={12} >
                        <Typography variant="subtitle1" color="textSecondary" align={"left"} className={classes.artistText}>
                            <Textfit mode="single" max={16} >
                                {this.state.currentTrack.artist}
                            </Textfit>
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <PlayPauseControl />
                    </Grid>
                    <Grid item xs={12}>
                        <TrackProgressControl track={this.state.currentTrack}/>
                    </Grid>
                </Grid>


            </Card>
        );
    }
}
export default withStyles(styles) (CurrentTrackPanel);
