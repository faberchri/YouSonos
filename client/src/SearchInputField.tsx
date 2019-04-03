import React from "react";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import TextField from '@material-ui/core/TextField';
import IconButton from '@material-ui/core/IconButton';

import CircularProgress from '@material-ui/core/CircularProgress';
import InputAdornment from '@material-ui/core/InputAdornment';

import Clear from '@material-ui/icons/Clear';

import {Subject, timer} from "rxjs";
import {debounce} from "rxjs/operators";

interface State {
    searchString: string
}

const styles = (theme: Theme) => createStyles({
    textField: {
        minHeight: '50px',
        width: '100%',
        marginTop: '12px',
        marginBottom: '8px',
    },
    circularProgress: {
        position: 'absolute'
    }
});

interface Props extends WithStyles<typeof styles> {
    onValueChange: (searchString: string) => void,
    indicateError: boolean,
    indicateSearchRunning: boolean
}

class SearchInputField extends React.Component<Props, State> {

    subject = new Subject<string>();

    constructor(props: Props) {
        super(props);
        this.state = {
            searchString: ''
        };

        this.subject
            .pipe(debounce(() => timer(500)))
            .subscribe((searchString) => {
                this.props.onValueChange(searchString)
            });
    }

    onChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const searchString = event.target.value;
        this.onFieldSet(searchString);
    };

    onReset = () => {
        this.onFieldSet('')
    };

    onFieldSet = (searchString: string) => {
        this.setState({
            searchString: searchString,
        });
        this.subject.next(searchString);
    };

    render() {

        const {classes} = this.props;

        let textFieldAction;
        if (this.props.indicateSearchRunning) {
            textFieldAction =
                <div>
                    <CircularProgress size={46} className={classes.circularProgress} />
                    <IconButton
                        aria-label="clear input"
                        onClick={this.onReset}>
                            <Clear/>
                    </IconButton>
                </div>
        } else {
            if (this.state.searchString.length > 0) {
                textFieldAction =
                    <IconButton
                        aria-label="clear input"
                        onClick={this.onReset}>
                        <Clear/>
                    </IconButton>
            }
        }

        let endAdornment;
        if (textFieldAction !== undefined) {
            endAdornment = {
                endAdornment: (
                    <InputAdornment position="end">
                        {textFieldAction}
                    </InputAdornment>
                ),
            };
        }

        return (
                <TextField
                    error={this.props.indicateError}
                    label="YouTube-URL, track id, playlist id, or keywords"
                    className={classes.textField}
                    margin="dense"
                    variant="outlined"
                    onChange={this.onChange}
                    value={this.state.searchString}
                    InputProps={endAdornment}
                />
        );
    }
}

export default withStyles(styles)(SearchInputField);
